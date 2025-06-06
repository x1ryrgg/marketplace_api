from rest_framework import serializers
from usercontrol_api.models import User
from seller_store_api.models import Store
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class SimpleCategorySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)

    def create(self, validated_data):
        return Category.objects.create(**validated_data)

    def validate_name(self, value):
        if 'category' not in value:
            raise serializers.ValidationError("Must be 'category' in name")
        return value



class SubCategorySerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Category.objects.all()
    )

    class Meta:
        model = SubCategory
        fields = ('id', 'category', 'name')


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=SubCategory.objects.all()
    )

    store = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Store.objects.all()
    )

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'store']


class VariantTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = VariantType
        fields = ('id', 'name')


class VariantOptionSerializer(serializers.ModelSerializer):
    variant = serializers.SlugRelatedField(
        slug_field='name',
        queryset=VariantType.objects.all()
    )

    class Meta:
        model = VariantOption
        fields = ('id', 'variant', 'value')


class ForPostProductVariantSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )
    options = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=VariantOption.objects.all()
    )

    class Meta:
        model = ProductVariant
        fields = ('id', 'product', 'price', 'quantity', 'options', 'image', 'description')

    def validate_options(self, options):
        """
        Валидация выбранных опций.
        Каждая категория VariantType может быть представлена только одной опцией.
        """
        option_types = {}
        for option in options:
            variant_type = option.variant.name
            if variant_type in option_types:
                raise serializers.ValidationError(
                    f"Для типа '{variant_type}' можно выбрать только одну опцию."
                )
            option_types[variant_type] = option
        return options


class ProductVariantSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    options = VariantOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ('id', 'product', 'price', 'quantity', 'options', 'image')


class SmallProductVariantSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    options = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=VariantOption.objects.all()
    )

    class Meta:
        model = ProductVariant
        fields = ('id', 'name', 'price', 'options', 'image')

    def get_name(self, obj):
        return obj.product.name if obj.product else None




