from rest_framework import serializers
from usercontrol_api.models import WishlistItem
from .models import *
from seller_store_api.models import Store
from product_control_api.models import ProductVariant
from product_control_api.serializers import ProductSerializer


class ProductVariantForWishListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ("id", "name", "price")

    def get_name(self, obj):
        return obj.product.name if obj.product else None


class WishListSerializer(serializers.ModelSerializer):
    product = ProductVariantForWishListSerializer(read_only=True)
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
    product = ProductVariantForWishListSerializer(read_only=True)

    class Meta:
        model = History
        fields = ['id', 'status', 'created_at', 'product', 'user_price', 'quantity']


class DeliverySerializer(serializers.ModelSerializer):
    product = ProductVariantForWishListSerializer(read_only=True)

    class Meta:
        model = Delivery
        fields = ("id", 'product', 'status', 'created_at', 'delivery_date', 'user_price', 'quantity')