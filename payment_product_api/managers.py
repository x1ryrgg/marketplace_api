from decimal import Decimal

from django.db import models
from django.db.models import Sum

from .models import *


class HistoryManager(models.Manager):

    def get_deliveries_total_sum(self, user):
        """ Возвращает количество успешно доставленных товаров для пользователя """
        result = self.filter(user=user, status='delivered').aggregate(total_sum=Sum('price'))
        return result['total_sum'] or 0

    def calculate_discount(self, user):
        total_sum = self.get_deliveries_total_sum(user)
        discount = 0

        discount += total_sum / 2000 * Decimal('0.01')
        return min(discount.__round__(3), 0.35)