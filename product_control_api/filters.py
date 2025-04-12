import django_filters
from .models import *


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method='filter_by_category')

    class Meta:
        model = Product
        fields = ['category']

    def filter_by_category(self, queryset, name, value):
        """Фильтрует товары по категории и её дочерним категориям."""
        try:
            category = Category.objects.get(name__icontains=value)
            categories = category.get_all_subcategories()
            return queryset.filter(category__in=categories)
        except Category.DoesNotExist:
            return queryset.none()