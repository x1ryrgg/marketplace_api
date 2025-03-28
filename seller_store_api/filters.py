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
            # Находим категорию по имени
            category = Category.objects.get(name__icontains=value)
            # Получаем все дочерние категории
            categories = category.get_all_subcategories()
            # Фильтруем товары по всем найденным категориям
            return queryset.filter(category__in=categories)
        except Category.DoesNotExist:
            # Если категория не найдена, возвращаем пустой QuerySet
            return queryset.none()
