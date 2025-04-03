from rest_framework import serializers
from usercontrol_api.models import WishlistItem
from .models import *
from seller_store_api.models import Product, Store


class ProductForWishListSerializer(serializers.ModelSerializer):
    store = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Store.objects.all()
    )

    class Meta:
        model = Product
        fields = ("id", "name", "price", "store")


class WishListSerializer(serializers.ModelSerializer):
    product = ProductForWishListSerializer(read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = WishlistItem
        fields = ['id', 'quantity', 'price', 'product']

    def get_price(self, obj):
        if obj.product:
            return obj.product.price * obj.quantity
        return None

    def to_representation(self, instance):
        if not instance.product:
            return {"detail": "Связанный продукт не найден."}
        return super().to_representation(instance)


class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = History
        fields = ['id', 'status', 'created_at', 'name', 'price', 'quantity']


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ("id", 'name', 'status', 'created_at', 'delivery_date', 'price', 'quantity')