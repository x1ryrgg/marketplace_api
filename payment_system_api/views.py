import hashlib
import uuid
from typing import Optional

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from yookassa.domain.notification import WebhookNotification

from usercontrol_api.serializers import PrivateUserSerializer
from usercontrol_api.views import _create_coupon_with_chance
from .serializers import *
from .services import UserBalanceService, PurchaseService
from .tasks import *


class WishListView(ModelViewSet):
    """Endpoint для просмотра своего списка желаемого и покупки товаров из этого списка
    url: /wishlist/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = WishListSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        return (
            WishlistItem.objects.filter(user=self.request.user)
            .select_related("product__product", "user")
            .prefetch_related("product__options")
        )

    def list(self, request, *args, **kwargs) -> Response:
        """Информация о списке желаемого пользователя"""
        queryset = self.get_queryset()
        serializer = WishListSummarySerializer(queryset, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """
        Изменение количества продукта в списке желаемого.
        URL: PATCH /wishlist/<int:id>/
        Body:
            - quantity (int, optional): Количество для изменения. По умолчанию 1.
            - symbol (str): '+' для увеличения; '-' для уменьшения.
        """
        wishlist_item = self.get_object()

        serializer = WishListItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_wishlist_item = serializer.update(wishlist_item, serializer.validated_data)

        if updated_wishlist_item is None:
            return Response(
                {"detail": _("Товар удален из корзины.")}, status=status.HTTP_200_OK
            )

        return Response(self.get_serializer(updated_wishlist_item).data)

    @action(methods=["post"], detail=False, url_path="buy")
    def payment_products(self, request, *args, **kwargs) -> Response:
        """транзакция покупки товаров
        url: /wishlist/buy/
        body: products (list, [] - по id товара, а не по id в списке желаемого)
        """
        products_ids = request.data.get("products", [])
        if not products_ids:
            raise ValidationError(_("Список товаров не может быть пустым."))

        # Вызываем сервис, передавая чистые данные
        purchace_service: PurchaseService = UserBalanceService(user=request.user, products_ids=products_ids)

        result = purchace_service.buy_products()

        user_data = PrivateUserSerializer(request.user).data
        return Response(
            {
                "message": _(
                    "Товар успешно оплачен. Проследить за ним вы сможете в доставках."
                ),
                "total_price": result["full_price"],
                "discount": f"Ваша скидка составляет {result['discount_percent']} %",
                "to_pay": result["discount_price"],
                "balance": f"Ваш баланс {user_data.get('balance')}",
            },
            status=status.HTTP_200_OK,
        )


class PayProductView(APIView):
    """Endpoint быстрой покупки 1 товара
    url: /products/<int:id>/buy/
    body: coupon (int, Optional)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PrivateUserSerializer

    def post(self, request, *args, **kwargs) -> Response:

        id = self.kwargs.get("id")
        product = get_object_or_404(ProductVariant, id=id)
        user = request.user

        coupon = 0
        coupon_code = int(request.data.get("coupon", 0))
        if coupon_code:
            try:
                coupon = Coupon.objects.get(user=user, code=coupon_code)
            except Coupon.DoesNotExist:
                raise ValidationError(
                    _(
                        "Купон с таким кодом не существует или принадлежит другому пользователю."
                    )
                )

        if product.quantity == 0:
            return Response(_("Продутка нет на складе."))

        price = product.price
        discount_price = _apply_discount_to_order(user, price, coupon)

        if discount_price > user.balance:
            return Response(
                _(
                    f"Недостаточно средств для произведения оплаты. Вам не хватает {product.price - user.balance}"
                )
            )

        with transaction.atomic():
            user.balance -= discount_price
            product.quantity -= 1

            Delivery.objects.create(
                user=user, product=product, user_price=discount_price, quantity=1
            )
            new_coupon = _create_coupon_with_chance(user)

            if coupon:
                coupon.delete()

            user.save()
            product.save()
            send_email_task.delay_on_commit(
                self.request.user.username, discount_price.quantize(Decimal("0.01"))
            )

            coupon_discount = Decimal(coupon.discount) if coupon else Decimal("0")
            base_discount = Decimal(History.objects.calculate_discount(user=user) * 100)
            total_discount = coupon_discount + base_discount

            user_data = self.serializer_class(user).data
            return Response(
                {
                    "сообщение": _(
                        "Товар успешно оплачен. Проследить за ним вы сможете в доставках."
                    ),
                    "цена товара": price,
                    "скидка": _(
                        f"Ваша персональная скидка составляет {History.objects.calculate_discount(user) * 100} %"
                    ),
                    "скидка купона": _(
                        f"{coupon.discount}%" if coupon else "Купон не применен."
                    ),
                    "суммарная скидка": _(f"{total_discount}%"),
                    "к оплате": discount_price,
                    "баланс": _(f"Ваш баланс {user_data.get("balance")}"),
                    "купон": _(
                        f"Поздравляю, вы получилики купон на скидку в {new_coupon.discount}%"
                        if new_coupon
                        else ""
                    ),
                }
            )


class HistoryView(ListAPIView):
    """Endpoint для просмотра истории покупок
    url: /history/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = HistorySerializer

    def get_queryset(self):
        return History.objects.filter(user=self.request.user).order_by("-created_at")


class DeliveryView(ModelViewSet):
    """Endpoint для проверки своих заказов, а так же выбор с обработкой товара
    url: /delivery/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = DeliverySerializer
    http_method_names = ["get", "post", "options"]

    def get_queryset(self):
        return (
            Delivery.objects.filter(user=self.request.user)
            .order_by("delivery_date")
            .select_related("user")
        )

    @action(detail=True, methods=["post"], url_path="take")
    def update_delivery(self, request, *args, **kwargs) -> Response:
        """
        POST-запрос, позволяющий выбирать, что делать с доставкой,
        когда товар уже пришел или еще в пути.
        url: /delivery/<int:delivery_id>/take/
        body: option (int, 1 -> (Принятие заказа) or 2 -> (Отказ))
        """
        delivery = self.get_object()
        user = request.user
        option = request.data.get("option")
        product = get_object_or_404(ProductVariant, id=delivery.product.id)

        if option not in (1, 2):
            raise ValidationError(
                _("Недопустимая опция. '1' - принять товар; '2' - отменить.")
            )

        # обработка если товар если он еще не пришел
        if delivery.status == "on the way" and option == 2:
            with transaction.atomic():
                user.balance += delivery.user_price
                user.save()
                product.quantity += delivery.quantity
                product.save(update_fields=["quantity"])
                History.objects.create(
                    user=user,
                    product=delivery.product,
                    user_price=delivery.product.price,
                    quantity=delivery.quantity,
                    status="denied",
                )
                delivery.delete()
                return Response(
                    _("Вы отменили заказ, сумма заказа перечисляется к вам обратно.")
                )

        if delivery.status == "on the way":
            raise ValidationError(_("Товар еще не доставлен."))

        # Обработка принятия или отмены товара
        status = "delivered" if option == 1 else "denied"
        message = (
            _(
                f"Товар {delivery.product.product.name} успешно принят! Заказывайте только у нас!"
            )
            if option == 1
            else _(
                f"Товар {delivery.product.product.name} отменен. Из-за политики нашего магазина вы не получите обратно сумму за товар, так как он уже доставлен."
            )
        )

        with transaction.atomic():
            if status == "denied":
                product.quantity += delivery.quantity
                product.save(update_fields=["quantity"])
            History.objects.create(
                user=user,
                product=delivery.product,
                user_price=delivery.user_price,
                quantity=delivery.quantity,
                status=status,
            )
            delivery.delete()
        return Response(message)


def _apply_discount_to_order(
    user: User, total_price: Decimal, coupon: Optional[Coupon] = None
) -> Decimal:
    """Применяет скидку пользователя к общей стоимости заказа"""
    discount = History.objects.calculate_discount(user)

    if coupon:
        discount += Decimal(coupon.discount / 100)

    discounted_price = total_price * Decimal(1 - discount)
    return discounted_price


""" TEST PAYMENT SYSTEM """


class CreatePaymentView(APIView):
    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save()

            # Генерация уникального order_id, если не указан
            if not payment.order_id:
                payment.order_id = str(uuid.uuid4())
                payment.save()

            # Параметры для PayBox
            params = {
                "pg_merchant_id": settings.PAYBOX_MERCHANT_ID,
                "pg_amount": str(payment.amount),
                "pg_order_id": payment.order_id,
                "pg_currency": payment.currency,
                "pg_description": payment.description,
                "pg_salt": str(uuid.uuid4()),  # Соль для подписи
                "pg_testing_mode": "1",  # 1 - тестовый режим, 0 - боевой
                "pg_result_url": f"{settings.SITE_URL}/api/paybox/result/",  # URL для уведомлений
                "pg_success_url": f"{settings.SITE_URL}/success/",  # URL после успешной оплаты
                "pg_failure_url": f"{settings.SITE_URL}/failed/",  # URL при ошибке
            }

            # Генерация подписи
            params_for_sig = [f"{key}={value}" for key, value in sorted(params.items())]
            params_for_sig.insert(0, "payment.php")
            params_for_sig.append(settings.PAYBOX_SECRET_KEY)
            signature_str = ";".join(params_for_sig)
            pg_sig = hashlib.md5(signature_str.encode()).hexdigest()

            params["pg_sig"] = pg_sig

            # Отправка запроса в PayBox
            paybox_url = "https://api.paybox.money/payment.php"
            response = requests.post(paybox_url, data=params)

            if response.status_code == 200:
                payment.paybox_payment_id = response.json().get("pg_payment_id", "")
                payment.save()
                return Response(
                    {"redirect_url": response.json().get("pg_redirect_url")}
                )
            else:
                return Response({"error": "PayBox error"}, status=400)
        return Response(serializer.errors, status=400)


@csrf_exempt
def paybox_callback(request):
    if request.method == "POST":
        data = request.POST
        pg_sig = data.get("pg_sig")

        # Проверка подписи
        params_for_sig = [
            f"{key}={value}" for key, value in sorted(data.items()) if key != "pg_sig"
        ]
        params_for_sig.append(settings.PAYBOX_SECRET_KEY)
        signature_str = ";".join(params_for_sig)
        calculated_sig = hashlib.md5(signature_str.encode()).hexdigest()

        if calculated_sig == pg_sig:
            order_id = data.get("pg_order_id")
            payment = Payment.objects.get(order_id=order_id)

            if data.get("pg_result") == "1":
                payment.status = "completed"
            else:
                payment.status = "failed"

            payment.save()
            return HttpResponse("OK", status=200)
        else:
            return HttpResponse("Invalid signature", status=400)
    return HttpResponse("Method not allowed", status=405)
