from django.db import transaction
from django.db.models import Count, Sum
from decimal import Decimal
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from .models import *
from usercontrol_api.models import User
from .serializers import *
from .serializers import *
from usercontrol_api.models import *
from seller_store_api.models import Product
from .tasks import *
from usercontrol_api.serializers import PrivateUserSerializer


class WishListView(ModelViewSet):
    """ Endpoint для просмотра своего списка желаемого и покупки товаров из этого списка
    url: /wishlist/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = WishListSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related('product', 'user')

    def list(self, request, *args, **kwargs):
        """ Информация о списке желаемого пользователя"""
        products_count = self.get_queryset().aggregate(Sum('quantity'))['quantity__sum'] or 0
        unique_products_count = self.get_queryset().count()
        products_total_count = 0

        for wishlist_item in self.get_queryset():
            product = wishlist_item.product
            quantity = wishlist_item.quantity
            sum_cost_product = quantity * product.price
            products_total_count += sum_cost_product
        products = self.get_queryset()
        data = {
            "Количество продуктов": products_count,
            "Количество уникальных продуктов": unique_products_count,
            "Общая стоимость": products_total_count,
            "Товары": self.get_serializer(products, many=True).data
        }
        return Response(data)

    def partial_update(self, request, *args, **kwargs):
        """ изменение количества продукта в списке желаемого
        url patch: /wishlist/<int:id>/
        body: quantity (int) or 1
        """
        wishlist_item = self.get_object()

        quantity = int(request.data.get('quantity', 1))

        if quantity <= 0:
            raise ValidationError(_("Количество должно быть больше 0."))

        if quantity >= wishlist_item.quantity:
            wishlist_item.delete()
            return Response(_("Товар удален из корзины."))

        wishlist_item.quantity -= quantity
        wishlist_item.save()
        return Response(_(f"Количество {wishlist_item.product} в корзине изменилось на {quantity}."))

    @staticmethod
    def calculate_total_price_and_validate(user, wishlist_items):
        """ Подсчет полной стоимости выбранных товаров с учетом их колличества """
        total_price = 0

        for wishlist_item in wishlist_items:
            product = wishlist_item.product
            quantity = wishlist_item.quantity
            sum_cost_product = quantity * product.price
            total_price += sum_cost_product

        if user.balance < total_price:
            raise ValidationError(
                _(f"Недостаточно средств. Вам не хватает {total_price - user.balance} руб.")
            )

        return total_price

    @action(methods=['post'], detail=False, url_path='buy')
    def payment_products(self, request, *args, **kwargs):
        """ транзакция покупки товаров
        url: /wishlist/buy/
        body: products (list, [])
        """
        user = request.user
        products_ids = request.data.get('products', [])

        if not products_ids:
            raise ValidationError(_("Список товаров не может быть пустым."))

        products = Product.objects.filter(id__in=products_ids).select_related('store', 'category')
        if len(products) != len(products_ids):
            invalid_ids = set(products_ids) - {p.id for p in products}
            raise ValidationError(_(f"Товары с ID {invalid_ids} не найдены."))

        wishlist_items = WishlistItem.objects.filter(user=user, product__in=products)
        wishlist_ids = set(item.product_id for item in wishlist_items)
        invalid_products = set(p.id for p in products if p.id not in wishlist_ids)
        if invalid_products:
            raise ValidationError(_(f'{invalid_products} - этого нет в вашей корзине'))

        full_price = self.calculate_total_price_and_validate(user, wishlist_items)

        discount_price = _apply_discount_to_order(user, full_price)

        if discount_price > user.balance:
            return Response(
                _(f"Недостаточно средств для произведения оплаты. Вам не хватает {discount_price - user.balance}"))

        with transaction.atomic():
            user.balance -= discount_price
            user.save()

            for item in wishlist_items:
                product = item.product
                if product.quantity < item.quantity:
                    raise ValidationError(_(f"Недостаточно товара {product.name} на складе."))

                product.quantity -= item.quantity
                product.save()
                sum_price = _apply_discount_to_order(user, product.price) * item.quantity

                send_email_task.delay(self.request.user.username, discount_price)
                Delivery.objects.create(user=user, name=product.name, price=sum_price, quantity=item.quantity)
            wishlist_items.delete()

            user_data = PrivateUserSerializer(user).data
            return Response({'сообщение': _("Товар успешно оплачен. Проследить за ним вы сможете в доставках."),
                             'цена товара': full_price,
                             "скидка": _(f"Ваша скидка составляет {History.objects.calculate_discount(user) * 100} %"),
                             "к оплате": discount_price,
                             'баланс': _(f"Ваш баланс {user_data.get('balance')}")
                             })


class HistoryView(ListAPIView):
    """ Endpoint для просмотра истории покупок
    url: /history/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = HistorySerializer

    def get_queryset(self):
        return History.objects.filter(user=self.request.user).order_by('-created_at')


class DeliveryView(ModelViewSet):
    """ Endpoint для проверки своих заказов, а так же выбор с обработкой товара
    url: /delivery/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DeliverySerializer
    http_method_names = ['get', 'post', 'options']

    def get_queryset(self):
        return Delivery.objects.filter(user=self.request.user).order_by('delivery_date').select_related('user')


    @action(detail=True, methods=['post'], url_path="take")
    def update_delivery(self, request, *args, **kwargs):
        """ POST-запрос, позволяющий выбирать, что делать с доставкой когда товар уже пришел, а так же когда он еще в пути
        url post: /delivery/<int:id>/take/
        body: option (1 or 2 int)
        """
        delivery = self.get_object()
        user = request.user
        option = int(request.data.get('option'))

        if option not in (1, 2):
            raise ValidationError(_("Недопустимая опция. '1' - принять товар; '2' - отменить."))

        # обработка если товар еще не пришел
        if delivery.delivery_date != date.today() and option == 2:
            with transaction.atomic():
                user.balance += delivery.price
                user.save()
                History.objects.create(user=user, name=delivery.name, price=delivery.price, quantity=delivery.quantity, status='denied')
                delivery.delete()
                return Response(_("Вы отменили заказ, сумма заказа перечисляется к вам обратно."))

        if delivery.delivery_date != date.today():
            raise ValidationError(_("Товар еще не доставлен."))

        # Обработка принятия или отмены товара
        status = 'delivered' if option == 1 else 'denied'
        message = (
            _(f"Товар {delivery.name} успешно принят! Заказывайте только у нас!") if option == 1
            else _(f"Товар {delivery.name} отменен. Из-за политики нашего магазина вы не получите обратно сумму за товар, так как он уже доставлен.")
        )

        with transaction.atomic():
            History.objects.create(user=user, name=delivery.name, price=delivery.price, quantity=delivery.quantity, status=status)
            delivery.delete()
        return Response(message)


def _apply_discount_to_order(user, total_price, coupon=None):
    """ Применяет скидку пользователя к общей стоимости заказа """
    discount = History.objects.calculate_discount(user)

    if coupon:
        discount += Decimal(coupon.discount / 100)

    discounted_price = total_price * Decimal(1 - discount)
    return discounted_price


def _create_coupon_with_chance(user):
    """ Создает купон с вероятностью 30% """
    if random.random() < 0.3:  # 30% шанс
        coupon = Coupon.objects.create(user=user)
        return coupon
    return None