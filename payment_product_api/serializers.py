from seller_store_api.serializers import ProductSerializer
from rest_framework import serializers
from usercontrol_api.models import WishlistItem
from .models import *


class WishListSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = WishlistItem
        fields = ['id', 'quantity', 'price', 'product']

    def get_price(self, obj):
        if obj.product:
            return obj.product.price
        return None

    def to_representation(self, instance):
        if not instance.product:
            return {"detail": "Связанный продукт не найден."}
        return super().to_representation(instance)


class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = History
        fields = ['id', 'name', 'price', 'quantity']