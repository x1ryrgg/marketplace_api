from datetime import date, timedelta
from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from .models import *
from usercontrol_api.models import User
from seller_store_api.permissions import IsSeller
from seller_store_api.models import Review
from seller_store_api.serializers import ReviewSerializer
from .serializers import *
from .permissions import *
from .filters import *
from usercontrol_api.models import *
from payment_system_api.models import *


class CategoriesView(ModelViewSet):
    """ Endpoint для создания категорий продуктов, их просмотра, изменения и удаления
    (доступно только superuser-ам, кроме SAFE_METHODS (get, options))
    url: /categories/
    body if post: name (str)
    """
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    serializer_class = CategorySerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'options']

    def get_queryset(self):
        return Category.objects.all()

    def destroy(self, request, *args, **kwargs) -> Response:
        category_id = self.kwargs.get('id')
        category = get_object_or_404(Category, id=category_id)
        self.perform_destroy(category)
        return Response(_(f"Категория с названием: {category.name} успешно удалена"))


class SubcategoriesView(ModelViewSet):
    """ Endpoint для создания подкатегорий продуктов, их просмотра, изменения и удаления
    (доступно только superuser-ам, кроме SAFE_METHODS (get, options))
    url: /subcategories/
    body if post: name (str), category (Category id)
    """
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    serializer_class = SubCategorySerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'options']

    def get_queryset(self):
        return SubCategory.objects.all()

    def destroy(self, request, *args, **kwargs) -> Response:
        category_id = self.kwargs.get('id')
        category = get_object_or_404(SubCategory, id=category_id)
        self.perform_destroy(category)
        return Response(_(f"Подкатегория с названием: {category.name} успешно удалена"))


class ProductOfSellerView(ModelViewSet):
    """ Endpoint для просмотра, добавления, изменения и удаления продуктов (для продавцов)
    url: /seller-products/
    body if post: name (str), category (Subcategory id),
                  price (Decimal), quantity (int), store (Store id), description (str - Optional)
    """
    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = ForPostProductVariantSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return ProductVariant.objects.filter(product__store__author=self.request.user).select_related('product').prefetch_related('options')

    def list(self, request, *args, **kwargs) -> Response:
        queryset = self.get_queryset()
        serializer = ProductVariantSerializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs) -> Response:
        product_id = self.kwargs.get('id')
        product = get_object_or_404(Product, id=product_id)
        self.perform_destroy(product)
        return Response(_(f"Продукт с названием: '{product.name}' из магазина {product.store.name} успешно удален."))


class ProductsView(ModelViewSet):
    """ Endpoint для просмотра всех продуктов.
    url: /products/?filter - возможность фильтровать продукты по стоимости (price__gt (больше), price__lt (меньше),
                             по названию (product), по опциям (options (Например цвет или размер) и по категориям (category)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductVariantSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'options']

    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductVariantFilter

    def get_queryset(self):
        # cache_key = f"filtered_data_{self.request.user.username}"
        # queryset = cache.get(cache_key)
        # if not queryset:
        #     queryset = ProductVariant.objects.all().select_related('product', 'product__category').prefetch_related('options').order_by("-views")
        #     queryset = self.filter_queryset(queryset)
        #     cache.set(cache_key, queryset, timeout=60)  # 60 сек
        # return queryset
        return ProductVariant.objects.all().select_related('product', 'product__category').prefetch_related('options').order_by("-views")

    def retrieve(self, request, *args, **kwargs) -> Response:
        product = self.get_object()
        product.views += 1
        product.save()
        serializer = self.get_serializer(product)

        comments = Review.objects.filter(product=product)
        comments_serializer = ReviewSerializer(comments, many=True)

        data = {
            'product': serializer.data,
            'comments': comments_serializer.data
        }
        return Response(data)

    @action(methods=['post'], detail=True, url_path='post_review')
    def write_review(self, request, *args, **kwargs) -> Response:
        """ Возможность оставить отзыв к товару (только те, кто его заказывал)
        url: /products/<int:product_id>/post_review/
        body:
            - body (str - Optional)
            - photo (url_path - Optional)
            - stars (int, range(1, 6)
        """
        product_id = self.kwargs.get('pk')
        product = get_object_or_404(ProductVariant, id=product_id)
        user = request.user
        user_history = History.objects.filter(product=product, user=user)

        body = request.data.get('body', None)
        stars = request.data.get('stars', None)
        photo = request.data.get('photo', None)

        if user_history:
            if stars is not None and (body or photo) is not None:
                review = Review.objects.create(user=user, product=product, body=body, photo=photo, stars=stars)
                review.save()

                return Response(ReviewSerializer(review, many=False).data)
            return Response(_("В отзыве вы должны оставить коментарий или прикрепить фото. Также укажите количество звезд."))
        return Response(_("Вы не можете оставлять отзыв под продуктами, которые не заказывали."))

    @action(methods=['patch'], detail=True, url_path=r'patch_review/(?P<review_id>\d+)') # сырые строки r'' - чтобы \ воспринимался как символ
    def edit_review(self, request, *args, **kwargs) -> Response:
        """ Изменение своего отзыва
        url: /products/<int: product_id>/put_review/<int: review_id>/
        """
        product_id = self.kwargs.get('pk')
        review_id = self.kwargs.get('review_id')
        product = get_object_or_404(ProductVariant, id=product_id)
        review = get_object_or_404(Review, id=review_id, product=product)

        if date.today() > review.created_at.date() + timedelta(days=3):
            return Response(_("Изменить коментарий можно только в первые 3 дня после его публикации "))

        body = request.data.get('body', review.body)
        stars = request.data.get('stars', review.stars)
        photo = request.data.get('photo', review.photo)

        if review.user != request.user:
            return Response(_("Вы не можете изменить чужой отзыв. "))

        if stars is not None and (body or photo) is not None:
            review.stars = stars
            review.body = body
            review.photo = photo
            review.save(update_fields=['stars', 'body', 'photo'])
            return Response(ReviewSerializer(review).data)
        return Response(_("В отзыве вы должны оставить комментарий или прикрепить фото. Также укажите количество звезд."))

    @action(methods=['delete'], detail=True, url_path=r'del_review/(?P<review_id>\d+)')
    def delete_review(self, request, *args, **kwargs) -> Response:
        """ Удаление своего отзыва
        url: /products/<int: product_id>/del_review/<int: review_id>/
        """
        product_id = self.kwargs.get('pk')
        review_id = self.kwargs.get('review_id')
        product = get_object_or_404(ProductVariant, id=product_id)
        review = get_object_or_404(Review, id=review_id, product=product)

        if review.user == request.user:
            review.delete()
            return Response(_(f"Отзыв с id: {review_id} успешно удален."))
        return Response(_("Вы не можете удалять чужие отзывы."))
