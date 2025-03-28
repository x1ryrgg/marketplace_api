from django.db.models import Count, Sum
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
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
from usercontrol_api.serializers import PrivateUserSerializer


text = f"Должность продавца даёт вам возможность заниматься бизнесом на этой площадке. {"\n"} Вы сможете выставлять свои магазины, а от них товары. {"\n"} Подробную информацию вы сможете узнать позвонив по номеру телефона: +8 800 555 35 35. Дайте ответ \"1\" для того, чтобы стать продавцом. "


class SellerRegisterView(ModelViewSet):
    """ EndPoint для определения пользователя продавцом."""
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
    """ EndPoint для регистрации магазина и проверки ваших магазинов """
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
    """ EndPoint показывающий все магазины, зарегестрированные на площадке.
    url: /stores/ - get
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StoreSerializer

    def get_queryset(self):
        return Store.objects.all()


class CategoriesView(ModelViewSet):
    """ EndPoint для создания категорий продуктов, их просмотра, изменения и удаления
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
    """ EndPoint для просмотра, добавления, изменения и удаления продуктов (для продавцов)
    url: /seller-products/
    body if post: name (str), price (float), quantity (int), category (str(name)), store (str(name))
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
    """ EndPoint для просмотра всех продуктов.
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
    permission_classes = [IsAuthenticated]
    serializer_class = PrivateUserSerializer

    def post(self, request, *args, **kwargs):
        id = self.kwargs.get('id')
        product = get_object_or_404(Product, id=id)
        user = request.user

        if product.price > user.balance:
            return Response(_("Недостаточно средств для произведения оплаты."))
        elif product.quantity == 0:
            return Response(_("Продутка нет на складе."))
        else:
            user.balance -= product.price
            product.quantity -= 1

            product.save()
            user.save()
            user_data = self.serializer_class(user).data
            return Response({'message': _("Товар успешно оплачен. Проследить за его доставкой вы сможете у себя в профиле."),
                             'balance': _(f"Ваш баланс {user_data.get("balance")}")
                             })


class WishListAddView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def post(self, request, *args, **kwargs):
        id = self.kwargs.get('id')
        product = get_object_or_404(Product, id=id)
        user = request.user

        user.wishlist.add(product)

        user_count_wishlist = user.wishlist.count()

        product_data = self.serializer_class(product).data
        return Response({'message': _(f"Продукт {product_data.get('name')} добавлен в корзину. "),
                         "quantity": _(f" Количество товаров в корзине: {user_count_wishlist}")
                         })


class WishListView(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    http_method_names = ['get', 'post']

    def get_queryset(self):
        return self.request.user.wishlist.all()

    def list(self, request, *args, **kwargs):
        products_count = self.get_queryset().count()
        products_total_count = self.get_queryset().aggregate(total_price=Sum('price'))['total_price'] or 0
        products = self.get_queryset()
        data = {
            "products_count": products_count,
            "products_total_count": products_total_count,
            "products": self.get_serializer(products, many=True).data
        }
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = self.get_serializer(product)
        return Response(serializer.data)

    def payment_products(self, request, *args, **kwargs):
        user = request.user

        products = request.data.get('products', [])
        products_to_pay = []
        products_to_pay_total_balance = 0
        for product_id in products:
            product = get_object_or_404(Product, id=product_id)
            products_to_pay.append(product)
            products_to_pay_total_balance += product.price

        invalid_products = [product.id for product in products_to_pay if product not in user.wishlist.all()]
        if invalid_products:
            raise ValidationError(_(f'{invalid_products} - этого нет в вашей корзине'))

        difference = user.balance - products_to_pay_total_balance
        if user.balance < products_to_pay_total_balance:
            raise ValidationError(_(f'Вам не хватает {difference}. '))

        user.wishlist.remove(*products_to_pay)
        user.balance -= products_to_pay_total_balance
        for product in products_to_pay:
            product.quantity -= 1
            product.save()
        user.save()
        return Response(_("Все чики пуки."))
# Надо сделать кароче корзину у пользователя чтобы он мог добавлять продукт в корзину,
# а там в корзине он уже мог выбирать нужные товары и оплачивать их, также нужно сделать, чтобы
# пользователь мог выбирать количество товаров.