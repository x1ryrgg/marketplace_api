from rest_framework import serializers
from usercontrol_api.models import User
from seller_store_api.models import Store
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    subcategory = serializers.SlugRelatedField(
        slug_field='name',  # Поле, которое нужно вернуть
        queryset=Category.objects.all(),  # Queryset для валидации входных данных
        required=False
    )

    class Meta:
        model = Category
        fields = ('id', 'name', 'subcategory')


class ProductOfSellerSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Category.objects.all()
    )

    store = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Store.objects.all()
    )

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'quantity', 'category', 'store', 'description', 'update_at', 'created_at')


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Category.objects.all()
    )

    store = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Store.objects.all()
    )

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category', 'store', 'quantity', 'description']