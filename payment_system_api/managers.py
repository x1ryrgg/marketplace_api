from decimal import Decimal

from django.db import models
from django.db.models import Sum


class HistoryManager(models.Manager):

    def get_deliveries_total_sum(self, user):
        """ Возвращает количество успешно доставленных товаров для пользователя """
        result = self.filter(user=user, status='delivered').aggregate(total_sum=Sum('price'))
        return result['total_sum'] or 0

    def calculate_discount(self, user):
        total_sum = self.get_deliveries_total_sum(user)
        discount = Decimal('0')

        # Преобразуем все значения в Decimal
        discount += total_sum / Decimal('2000') * Decimal('0.01')
        return min(discount.quantize(Decimal('0.01')), Decimal('0.35'))