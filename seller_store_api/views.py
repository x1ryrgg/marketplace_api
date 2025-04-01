from django.db import transaction
from django.db.models import Count, Sum
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
from .permissions import *
from .filters import *
from usercontrol_api.models import *

from usercontrol_api.serializers import PrivateUserSerializer


text = f"Должность продавца даёт вам возможность заниматься бизнесом на этой площадке. {"\n"} Вы сможете выставлять свои магазины, а от них товары. {"\n"} Подробную информацию вы сможете узнать позвонив по номеру телефона: +8 800 555 35 35. Дайте ответ \"1\" для того, чтобы стать продавцом. "


class SellerRegisterView(ModelViewSet):
    """ Endpoint для определения пользователя продавцом."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    http_method_names = ['get', 'put']

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        """
        Проверка пользователя на наличие опций продавца.
        url: /seller/register/ - get
        """
        queryset = self.get_queryset()
        user = queryset.first()
        if user.is_seller:
            return Response(_("Вы являетесь продавцом на этой площадке."))
        return Response(_("Вы не являетесь продавцом."))

    def get_object(self):
        return self.get_queryset().get()

    def update(self, request, *args, **kwargs):
        """
        Возможность стать продавцом на площадке
        url: /seller/register/ - put
        body: option (str(int))
        """
        option = request.data.get("option")
        user = self.get_object()
        if not option:
            return Response(_("Нужно указать свой ответ. 1 - Стать продавцом."))

        if option == '1':
            user.is_seller = True
            user.save()
            return Response(_("Поздравляю, вам открыта возможноть выставлять свои магазины, а также товары на площадке."))
        else:
            return Response(_(text))


class StoreView(ModelViewSet):
    """ Endpoint для регистрации магазина и проверки ваших магазинов """
    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = StoreSerializer
    http_method_names = ['get', 'post']

    def get_queryset(self):
        """
        Возвращает магазины, у которых пользователь является автором.
        url: /store/ - get
        """
        return Store.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        """
        Регистрация магазина
        url: /store/ - post
        body: name (str), description (str), city (str), email (str if need)
        """
        count_stores = Store.objects.filter(author=self.request.user).count()
        if count_stores >= 3:
            raise Exception(_('Пользователь может регестировать до 3 магазинов.'))
        else:
            serializer.save(author=self.request.user)


class StoresAllView(ListAPIView):
    """ Endpoint показывающий все магазины, зарегестрированные на площадке.
    url: /stores/ - get
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StoreSerializer

    def get_queryset(self):
        return Store.objects.all()


class CategoriesView(ModelViewSet):
    """ Endpoint для создания категорий продуктов, их просмотра, изменения и удаления
    (доступно только администраторам, кроме SAFE_METHODS)
    url: /categories/
    body if post: name (str), subcategory (str if need)
    """
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    serializer_class = CategorySerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'id'

    def get_queryset(self):
        return Category.objects.all()

    def destroy(self, request, *args, **kwargs):
        category_id = self.kwargs.get('id')
        category = get_object_or_404(Category, id=category_id)
        self.perform_destroy(category)
        return Response(_(f"Категория с названием: {category.name} успешно удалена"))


class ProductOfSellerView(ModelViewSet):
    """ Endpoint для просмотра, добавления, изменения и удаления продуктов (для продавцов)
    url: /seller-products/
    body if post: name (str), price (float), quantity (int), category (str(name)), store (str(name)), description (str if need)
    """
    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = ProductOfSellerSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'id'

    def get_queryset(self):
        return Product.objects.filter(store__author=self.request.user).select_related('store', 'category')

    def destroy(self, request, *args, **kwargs):
        product_id = self.kwargs.get('id')
        product = get_object_or_404(Product, id=product_id)
        self.perform_destroy(product)
        return Response(_(f"Продукт с названием: '{product.name}' из магазина {product.store.name} успешно удален."))


class ProductsView(ModelViewSet):
    """ Endpoint для просмотра всех продуктов.
    url: /products/?category= (filter-icontains)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    http_method_names = ['get']

    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_queryset(self):
        return Product.objects.all().select_related('store', 'category')


class PayProductView(APIView):
    """ Endpoint для покупик товара
    url: /products/<int:id>/buy/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PrivateUserSerializer

    def post(self, request, *args, **kwargs):
        id = self.kwargs.get('id')
        product = get_object_or_404(Product, id=id)
        user = request.user

        if product.price > user.balance:
            return Response(_(f"Недостаточно средств для произведения оплаты. Вам не хватает {product.price - user.balance}"))
        elif product.quantity == 0:
            return Response(_("Продутка нет на складе."))

        with transaction.atomic():
            user.balance -= product.price
            product.quantity -= 1
            product.save()

            history_of_product = History.objects.create(user=user, name=product.name, price=product.price, quantity=1)
            history_of_product.save()
            user.save()
            user_data = self.serializer_class(user).data
            return Response({'message': _("Товар успешно оплачен. Проследить за его доставкой вы сможете у себя в профиле."),
                             'balance': _(f"Ваш баланс {user_data.get("balance")}")
                             })


class WishListAddView(APIView):
    """ Endpoint для добавления товаров с список желаемого
    url: /products/<int:id>/add/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def post(self, request, *args, **kwargs):
        id = self.kwargs.get('id')
        quantity = request.data.get('quantity', 1)

        product = get_object_or_404(Product, id=id)
        user = request.user

        wishlist_item, created = WishlistItem.objects.get_or_create(user=user,product=product,defaults={'quantity': quantity})

        if not created:
            wishlist_item.quantity += quantity
            wishlist_item.save()

        product_data = self.serializer_class(product).data
        total_quantity = WishlistItem.objects.aggregate(Sum('quantity'))['quantity__sum']
        return Response({'message': _(f"Продукт {product_data.get('name')} добавлен в корзину. "),
                         "quantity": _(f" Количество товаров в корзине: {total_quantity}")
                         })


class WishListView(ModelViewSet):
    """ Endpoint для просмотра своего списка желаемого и покупки товаров из этого списка
    url: /wishlist/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = WishListSerializer
    http_method_names = ['get', 'post']

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        # products_count = self.get_queryset().count()
        # products_total_count = self.get_queryset().aggregate(total_price=Sum('price'))['total_price'] or 0
        # products = self.get_queryset()
        # data = {
        #     "products_count": products_count,
        #     "products_total_count": products_total_count,
        #     "products": self.get_serializer(products, many=True).data
        # }
        queryset = self.get_queryset()  # Получаем QuerySet
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @staticmethod
    def calculate_total_price_and_validate(user, wishlist_items):
        """ Подсчет полной стоимости выбранных товаров с учетом их колличества """
        total_price = 0

        # Перебираем только элементы списка желаний
        for wishlist_item in wishlist_items:
            product = wishlist_item.product  # Получаем связанный товар
            quantity = wishlist_item.quantity  # Получаем количество
            sum_cost_product = quantity * product.price  # Считаем стоимость
            total_price += sum_cost_product  # Добавляем к общей сумме

        # Проверяем баланс пользователя
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

        total_price = self.calculate_total_price_and_validate(user, wishlist_items)

        with transaction.atomic():
            user.balance -= total_price
            user.save()

            for item in wishlist_items:
                product = item.product
                if product.quantity < item.quantity:
                    raise ValidationError(_(f"Недостаточно товара {product.name} на складе."))

                product.quantity -= item.quantity  # Вычитаем нужное количество
                product.save()
                History.objects.create(user=user, name=product.name, price=product.price, quantity=item.quantity)

            wishlist_items.delete()
        return Response(_("Товары успешно оплачены. Информацию о заказе вы сможете посмотреть в доставках."))


class HistoryView(ListAPIView):
    """ Endpoint для просмотра истории покупок
    url: /history/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = HistorySerializer

    def get_queryset(self):
        return History.objects.filter(user=self.request.user).order_by('-created_at')