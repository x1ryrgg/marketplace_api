from rest_framework import serializers
from usercontrol_api.models import User
from .models import *


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_seller')


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    subcategory = serializers.SlugRelatedField(
        slug_field='name',  # Поле, которое нужно вернуть
        queryset=Category.objects.all(),  # Queryset для валидации входных данных
        allow_null=True  # Разрешить null, если подкатегория не указана
    )

    class Meta:
        model = Category
        fields = ('name', 'subcategory')