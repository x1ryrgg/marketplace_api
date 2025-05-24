import django_filters
from django_filters import ModelMultipleChoiceFilter, ModelChoiceFilter
from .models import *


class UserFiler(django_filters.FilterSet):
    username = django_filters.CharFilter(field_name='username', lookup_expr='iexact')
    tg_id = django_filters.CharFilter(field_name='tg_id', lookup_expr='iexact')

    class Meta:
        model = User
        fields = ('tg_id', 'username')