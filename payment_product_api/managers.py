from django.db import models
from .models import *


class HistoryManager(models.Manager):

    def get_deliveries_count(self, user):
        """ Возвращает количество успешно доставленных товаров для пользователя """
        return self.filter(user=user, status='delivered').count()

    def calculate_discount(self, user):
        deliveries = self.get_deliveries_count(user)
        discount = 0

        if deliveries >= 70:
            return 0.35

        discount += (deliveries // 2) / 100
        return min(discount, 0.35)