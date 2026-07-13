from typing import List, Optional

from django.db import transaction
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from product_control_api.models import ProductVariant
from usercontrol_api.views import _create_coupon_with_chance
from .models import Delivery, History
from usercontrol_api.models import WishlistItem, User, Coupon
from payment_system_api.dependencies import _apply_discount_to_order
from payment_system_api.tasks import send_email_task
from abc import abstractmethod, ABC


class PurchaseService(ABC):
    def __init__(self, user: User,
                 products_ids: List[int],
                 discount_price: Optional[Decimal] = None,
                 coupon: Optional[Coupon] = None,):
        self.user = user
        self.products_ids = products_ids
        self.discount_price = discount_price
        self.coupon = coupon


    @abstractmethod
    def send_email_check(self):
        """Отправка чека на почту"""
        pass

    @abstractmethod
    def buy_products(self):
        """Основная логика списания и оформления доставки"""
        pass


class UserBalanceService(PurchaseService):

    def send_email_check(self):
        price_to_send = self.discount_price or Decimal("0.00")
        return send_email_task.delay_on_commit(
                    self.user.username, price_to_send.quantize(Decimal("0.01"))
                )

    def buy_products(self):
        # 1. Загружаем и проверяем товары
        if not self.products_ids:
            raise ValidationError(_("Список товаров не может быть пустым."))

        # Жесткое ограничение: купон только для ОДНОГО товара
        if self.coupon and len(self.products_ids) > 1:
            raise ValidationError(_("Купон можно применить только при покупке одного товара."))

        products = (
            ProductVariant.objects.filter(id__in=self.products_ids)
            .select_related("product", "product__category")
            .prefetch_related("options")
        )
        if len(products) != len(self.products_ids):
            invalid_ids = set(self.products_ids) - {p.id for p in products}
            raise ValidationError(_(f"Товары с ID {invalid_ids} не найдены."))

        # 2. Считаем общую базовую цену
        wishlist_items = WishlistItem.objects.filter(
            user=self.user, product_id__in=self.products_ids
        ).select_related("product")

        wishlist_dict = {item.product_id: item.quantity for item in wishlist_items}
        if wishlist_dict:
            full_price = sum(quantity * product.price for product, quantity in ((p, wishlist_dict[p.id]) for p in products))
        else:
            # Если быстрая покупка (в корзине пусто), берем цену 1 штуки товара
            full_price = sum(product.price for product in products)

        self.discount_price = _apply_discount_to_order(self.user, full_price, self.coupon)

        if self.user.balance < self.discount_price:
            raise ValidationError(
                _(f"Недостаточно средств. Не хватает {self.discount_price - self.user.balance} руб.")
            )

        # 3. Валидация склада с учетом источника покупки
        for product in products:
            needed_quantity = wishlist_dict.get(product.id, 1)
            if product.quantity < needed_quantity:
                raise ValidationError(
                    _(f"Недостаточно товара {product.product.name} на складе.")
                )

        discount_coefficient = self.discount_price / full_price if full_price > 0 else Decimal("1.0")

        # 4. Проведение транзакции
        with transaction.atomic():
            self.user.balance -= self.discount_price
            self.user.save(update_fields=["balance"])

            if self.coupon:
                self.coupon.delete()

            for product in products:
                needed_quantity = wishlist_dict.get(product.id, 1)

                product.quantity -= needed_quantity
                product.save(update_fields=["quantity"])

                sum_price = (product.price * needed_quantity * discount_coefficient).quantize(Decimal("0.01"))

                Delivery.objects.create(
                    user=self.user,
                    product=product,
                    user_price=sum_price,
                    quantity=needed_quantity,
                )

            # Шанс на создание купона пользователю
            new_coupon = _create_coupon_with_chance(self.user)

            # Celery таска отправится только ПОСЛЕ успешного коммита транзакции
            self.send_email_check()

            # Очищаем купленное из корзины
            if wishlist_items.exists():
                wishlist_items.delete()

        return {
            "full_price": full_price,
            "discount_price": self.discount_price,
            "discount_percent": History.objects.calculate_discount(self.user) * 100,
            "coupon_added": True if new_coupon else False,
        }
