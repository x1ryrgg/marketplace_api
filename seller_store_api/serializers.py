from rest_framework import serializers
from usercontrol_api.models import User
from .models import *
from usercontrol_api.models import WishlistItem


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_seller')


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    product = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Product.objects.all()
    )

    class Meta:
        model = Review
        fields = ("id", 'user', 'product', 'stars', 'body', 'photo', 'created_at')

