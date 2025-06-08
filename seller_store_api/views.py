from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from payment_system_api.models import *
from product_control_api.serializers import (
    SmallProductVariantSerializer,
)
from .permissions import *
from .serializers import *

text = f"Должность продавца даёт вам возможность заниматься бизнесом на этой площадке. {"\n"} Вы сможете выставлять свои магазины, а от них товары. {"\n"} Подробную информацию вы сможете узнать позвонив по номеру телефона: +8 800 555 35 35. Дайте ответ \"1\" для того, чтобы стать продавцом. "


class SellerRegisterView(ModelViewSet):
    """Endpoint для определения пользователя продавцом
    url: /seller/register/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    http_method_names = ["get", "put"]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def list(self, request, *args, **kwargs) -> Response:
        queryset = self.get_queryset()
        user = queryset.first()
        if user.is_seller:
            return Response(_("Вы являетесь продавцом на этой площадке."))
        return Response(
            _(
                "Вы не являетесь продавцом. Нужно оплатить доступ к привилегиям продавца, цена - 10000 руб. "
            )
        )

    def get_object(self):
        return self.get_queryset().get()

    def update(self, request, *args, **kwargs) -> Response:
        """Возможность стать продавцом на площадке
        url: /seller/register/ - put
        body: option (str (int))
        """
        option = request.data.get("option")
        user = self.get_object()
        if not option:
            return Response(_("Нужно указать свой ответ. 1 - Стать продавцом."))
        if user.is_seller:
            return Response(_("Вы уже являетесь продавцом."))

        if option == 1:
            cost = Decimal("10000")
            if user.balance >= cost:
                with transaction.atomic():
                    user.balance -= cost
                    user.is_seller = True
                    user.save(update_fields=["is_seller", "balance"])
                    return Response(_('Поздравляю! Вам доступны привилегии продавца.'))
            return Response(_(f"Вам не хватает {cost - user.balance}"))
        else:
            return Response(_(text))


class StoreView(ModelViewSet):
    """Endpoint для регистрации магазина и просмотра ваших магазинов
    url: /store/
    """

    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = StoreSerializer
    http_method_names = [
        "get",
        "post",
    ]

    def get_queryset(self):
        return Store.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        """Регистрация магазина
        body: name (str), description (str - Optional), city (str), email (str - Optional)
        """
        user = self.request.user
        count_stores = Store.objects.filter(author=user).count()
        if count_stores >= 3:
            raise Exception(_("Пользователь может регистировать до 3 магазинов."))
        else:
            serializer.save(author=user)


class StoresAllView(ModelViewSet):
    """Endpoint показывающий все магазины, зарегестрированные на площадке.
    url: /stores/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = StoreSerializer

    def get_queryset(self):
        return Store.objects.all()

    def retrieve(self, request, *args, **kwargs) -> Response:
        store = self.get_object()
        products = ProductVariant.objects.filter(product__store=store)
        data = {
            "store": self.get_serializer(store, many=False).data,
            "products": SmallProductVariantSerializer(products, many=True).data,
        }
        return Response(data)


class WishListAddView(APIView):
    """Endpoint для добавления товаров в список желаемого
    url: /products/<int: product_id>/add/
    body: quantity (int - Optional) or 1
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SmallProductVariantSerializer

    def post(self, request, *args, **kwargs) -> Response:
        id = self.kwargs.get("id")
        quantity = request.data.get("quantity", 1)

        product = get_object_or_404(ProductVariant, id=id)
        user = request.user

        wishlist_item, created = WishlistItem.objects.get_or_create(
            user=user, product=product, defaults={"quantity": quantity}
        )

        if not created:
            wishlist_item.quantity += quantity
            wishlist_item.save(update_fields=["quantity"])

        product_data = self.serializer_class(product).data
        total_quantity = WishlistItem.objects.filter(user=user).aggregate(
            Sum("quantity")
        )["quantity__sum"]
        return Response(
            {
                "сообщение": _(
                    f"Продукт {product_data.get('name')} добавлен в корзину."
                ),
                "добавлено": _(f"Было добавлено товаров: {quantity}"),
                "список желаемого": _(
                    f"Количество товаров в списке желаемого: {total_quantity}"
                ),
            }
        )


# class SetCookie(APIView):
#     def get(self, request):
#         response = Response({"message": "Cookie complete!"})
#         response.set_cookie('status', 'YeCookie', httponly=True, max_age=3600)
#         return response
#
#
# class GetCookie(APIView):
#     def get(self, request):
#         status = request.COOKIES.get('status', "NoCookie")
#         return Response(f"Condition: {status}")
#
#
# class DelCookie(APIView):
#     def get(self, request):
#         response = Response("Cookie deleted!")
#         response.delete_cookie('status')
#         return response
