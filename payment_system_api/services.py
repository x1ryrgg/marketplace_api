from typing import List, Optional

from django.db import transaction
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from product_control_api.models import ProductVariant
from .models import Delivery, History
from usercontrol_api.models import WishlistItem, User, Coupon
from payment_system_api.dependencies import _apply_discount_to_order
from payment_system_api.tasks import send_email_task
from abc import abstractmethod, ABC


class PurchaseService(ABC):
    def __init__(self, user: User, products_ids: List[int], discount_price: Optional[Decimal] = None):
        self.user = user
        self.products_ids = products_ids
        self.discount_price = discount_price

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

        products = (
            ProductVariant.objects.filter(id__in=self.products_ids)
            .select_related("product", "product__category")
            .prefetch_related("options")
        )
        if len(products) != len(self.products_ids):
            invalid_ids = set(self.products_ids) - {p.id for p in products}
            raise ValidationError(_(f"Товары с ID {invalid_ids} не найдены."))

        # 2. Считаем цену (уже по оптимизированному кверисету)
        wishlist_items = WishlistItem.objects.filter(
            user=self.user, product_id__in=self.products_ids
        ).select_related("product")

        if not wishlist_items:
            raise ValidationError(_("Выбранных товаров нет в вашей корзине."))

        full_price = sum(item.quantity * item.product.price for item in wishlist_items)
        self.discount_price = _apply_discount_to_order(self.user, full_price)

        if self.user.balance < self.discount_price:
            raise ValidationError(
                _(
                    f"Недостаточно средств. Не хватает {self.discount_price - self.user.balance} руб."
                )
            )

        # 3. Валидация склада ДО транзакции
        for item in wishlist_items:
            if item.product.quantity < item.quantity:
                raise ValidationError(
                    _(f"Недостаточно товара {item.product.product.name} на складе.")
                )

        # 4. Проведение транзакции
        with transaction.atomic():
            self.user.balance -= self.discount_price
            self.user.save()

            for item in wishlist_items:
                product = item.product
                product.quantity -= item.quantity
                product.save(update_fields=["quantity"])

                sum_price = (
                    _apply_discount_to_order(self.user, product.price) * item.quantity
                )

                Delivery.objects.create(
                    user=self.user,
                    product=product,
                    user_price=sum_price,
                    quantity=item.quantity,
                )

            # Celery таска отправится только ПОСЛЕ успешного коммита транзакции
            self.send_email_check()

            # Очищаем купленное из корзины
            wishlist_items.delete()

        return {
            "full_price": full_price,
            "discount_price": self.discount_price,
            "discount_percent": History.objects.calculate_discount(self.user) * 100,
        }
