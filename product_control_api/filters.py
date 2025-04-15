import django_filters
from django_filters import ModelMultipleChoiceFilter, ModelChoiceFilter

from .models import *


# class ProductFilter(django_filters.FilterSet):
#     category = django_filters.CharFilter(method='filter_by_category')
#
#     class Meta:
#         model = ProductVariant
#         fields = ['category']
#
#     def filter_by_category(self, queryset, name, value):
#         """Фильтрует товары по категории и её дочерним категориям."""
#         try:
#             category = Category.objects.get(name__icontains=value)
#             categories = category.get_all_subcategories()
#             return queryset.filter(category__in=categories)
#         except Category.DoesNotExist:
#             return queryset.none()


class ProductVariantFilter(django_filters.FilterSet):
    price__gt = django_filters.NumberFilter(field_name='price', lookup_expr='gt') # больше
    price__lt = django_filters.NumberFilter(field_name='price', lookup_expr='lt') # меньше

    product = django_filters.CharFilter(field_name='product__name', lookup_expr='icontains')

    options = django_filters.CharFilter(field_name='options__value', lookup_expr='icontains', label='Опции')

    category = django_filters.CharFilter(field_name='product__category__name', lookup_expr='icontains', label='Категория')

    class Meta:
        model = ProductVariant
        fields = ()