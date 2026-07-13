from django.db.models import F, Sum
from rest_framework import serializers
from usercontrol_api.models import WishlistItem
from .models import *
from seller_store_api.models import Store
from product_control_api.models import ProductVariant
from product_control_api.serializers import ProductSerializer


class ProductVariantForWishListSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="product.name")

    class Meta:
        model = ProductVariant
        fields = ("id", "name", "price")


class WishListSerializer(serializers.ModelSerializer):
    product = ProductVariantForWishListSerializer(read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = WishlistItem
        fields = ['id', 'quantity', 'price', 'product']

    def get_price(self, obj):
        return obj.product.price * obj.quantity if obj.product else 0

    def to_representation(self, instance):
        return super().to_representation(instance)


class WishListSummarySerializer(serializers.Serializer):
    summary_count = serializers.SerializerMethodField()
    unique_products_count = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    def get_summary_count(self, obj):
        # obj — это отфильтрованный QuerySet из элементов WishlistItem
        return obj.aggregate(total=Sum("quantity"))["total"] or 0

    def get_unique_products_count(self, obj):
        return obj.count()

    def get_total_cost(self, obj):
        # Перемножаем количество на цену варианта товара
        result = obj.annotate(item_cost=F("quantity") * F("product__price")).aggregate(
            total_sum=Sum("item_cost")
        )
        return result["total_sum"] or 0

    def get_items(self, obj):
        return WishListSerializer(obj, many=True, context=self.context).data


class WishListItemUpdateSerializer(serializers.Serializer):
    """Сериализатор для обработки PATCH-запроса (изменение количества)"""

    quantity = serializers.IntegerField(min_value=1, default=1)
    symbol = serializers.ChoiceField(choices=["+", "-"])

    def update(self, instance, validated_data):
        quantity = validated_data["quantity"]
        symbol = validated_data["symbol"]

        if symbol == "+":
            instance.quantity += quantity
            instance.save(update_fields=["quantity"])
        elif symbol == "-":
            if instance.quantity <= quantity:
                instance.delete()
                return None  # Флаг, что объект удален
            instance.quantity -= quantity
            instance.save(update_fields=["quantity"])

        return instance


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


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['amount', 'currency', 'order_id', 'description']
