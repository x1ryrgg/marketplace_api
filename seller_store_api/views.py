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
from payment_system_api.models import *
from usercontrol_api.serializers import PrivateUserSerializer
from payment_system_api.views import _apply_discount_to_order
from usercontrol_api.views import _create_coupon_with_chance
from payment_system_api.tasks import send_email_task


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
        option = int(request.data.get("option"))
        user = self.get_object()
        if not option:
            return Response(_("Нужно указать свой ответ. 1 - Стать продавцом."))

        if option == 1:
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
            raise Exception(_('Пользователь может регистировать до 3 магазинов.'))
        else:
            serializer.save(author=self.request.user)


class StoresAllView(ModelViewSet):
    """ Endpoint показывающий все магазины, зарегестрированные на площадке.
    url: /stores/ - get
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StoreSerializer

    def get_queryset(self):
        return Store.objects.all()

    def retrieve(self, request, *args, **kwargs):
        store = self.get_object()
        products = Product.objects.filter(store=store)
        data = {
            'store': self.get_serializer(store, many=False).data,
            'products': ProductSerializer(products, many=True).data
        }
        return Response(data)


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
    http_method_names = ['get', 'post', 'put', 'delete', 'options']

    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_queryset(self):
        return Product.objects.all().select_related('store', 'category')

    def retrieve(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = self.get_serializer(product)

        comments = Review.objects.filter(product=product)
        comments_serializer = ReviewSerializer(comments, many=True)

        data = {
            'product': serializer.data,
            'comments': comments_serializer.data
        }
        return Response(data)

    @action(methods=['post'], detail=True, url_path='write')
    def write_review(self, request, *args, **kwargs):
        product_id = self.kwargs.get('pk')
        product = get_object_or_404(Product, id=product_id)
        user = request.user
        user_history = History.objects.filter(product=product, user=user)

        body = request.data.get('body', None)
        stars = request.data.get('stars', None)
        photo = request.data.get('photo', None)

        if user_history:
            if stars is not None and (body or photo) is not None:
                comment = Review.objects.create(user=user, product=product, body=body, photo=photo, stars=stars)
                comment.full_clean()
                comment.save()
                return Response(_(f"Отзыв к {product.name} успешно оставлен."))
            return Response(_("В отзыве вы должны оставить коментарий или прикрепить фото. Также укажите количество звезд."))
        return Response(_("Вы не можете оставлять отзыв под продуктами, которые не заказывали."))

    @action(methods=['put'], detail=True, url_path='edit/(?P<review_id>\d+)')
    def edit_review(self, request, *args, **kwargs):
        product_id = self.kwargs.get('pk')
        review_id = self.kwargs.get('review_id')
        product = get_object_or_404(Product, id=product_id)
        review = get_object_or_404(Review, id=review_id, product=product)

        body = request.data.get('body', review.body)
        stars = request.data.get('stars', review.stars)
        photo = request.data.get('photo', review.photo)

        if review.user != request.user:
            return Response(_("Вы не можете изменить чужой отзыв. "))

        if stars is not None and (body or photo) is not None:
            review.stars = stars
            review.body = body
            review.photo = photo
            review.full_clean()
            review.save()
            return Response(_("Комментарий успешно обнавлен!"))
        return Response(_("В отзыве вы должны оставить комментарий или прикрепить фото. Также укажите количество звезд."))

    @action(methods=['delete'], detail=True, url_path='delete/(?P<review_id>\d+)')
    def delete_review(self, request, *args, **kwargs):
        product_id = self.kwargs.get('pk')
        review_id = self.kwargs.get('review_id')
        product = get_object_or_404(Product, id=product_id)
        review = get_object_or_404(Review, id=review_id, product=product)

        if review.user == request.user:
            review.delete()
            return Response(_(f"Отзыв с id {review_id} успешно удален."))
        return Response(_("Вы не можете удалять чужие отзывы."))


class WishListAddView(APIView):
    """ Endpoint для добавления товаров с список желаемого
    url: /products/<int:id>/add/
    body: quantity (int) or 1
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def post(self, request, *args, **kwargs):
        id = self.kwargs.get('id')
        quantity = request.data.get('quantity', 1)

        product = get_object_or_404(Product, id=id)
        user = request.user

        wishlist_item, created = WishlistItem.objects.get_or_create(user=user,product=product, defaults={'quantity': quantity})

        if not created:
            wishlist_item.quantity += quantity
            wishlist_item.save()

        product_data = self.serializer_class(product).data
        total_quantity = WishlistItem.objects.filter(user=user).aggregate(Sum('quantity'))['quantity__sum']
        return Response({'сообщение': _(f"Продукт {product_data.get('name')} добавлен в корзину. "),
                         "добавлено": _(f"Было добавлено товаров: {quantity} "),
                         "список желаемого": _(f" Количество товаров в списке желаемого: {total_quantity}")
                         })


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