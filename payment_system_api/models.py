from django.db import models

from seller_store_api.models import Product
from usercontrol_api.models import User
import datetime
import random
from .managers import *


class DeliveryType(models.TextChoices):
    ON_THE_WAY = ('on the way', 'в пути')
    DELIVERED = ('delivered', 'доставлено')
    DENIED = ('denied', 'отказано')


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    user_price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    quantity = models.PositiveIntegerField(null=False, blank=True, default=1)
    status = models.CharField(choices=DeliveryType, default=DeliveryType.DELIVERED, max_length=10)
    created_at = models.DateField(auto_now_add=True)

    objects = HistoryManager()

    def __str__(self):
        return "User %s | Name %s | Price %s | Quantity %s" % (self.user.username, self.product.name, self.user_price, self.quantity)

    @staticmethod
    def get_status(queryset):
        return [i.status for i in queryset]


class Delivery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    user_price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    quantity = models.PositiveIntegerField(null=False, blank=True, default=1)
    status = models.CharField(choices=DeliveryType, default=DeliveryType.ON_THE_WAY, max_length=10)
    created_at = models.DateField(auto_now_add=True)
    delivery_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
        if not self.delivery_date:
            self.delivery_date = self.created_at + datetime.timedelta(days=random.randint(0, 9))
        super().save(update_fields=['delivery_date'])

    def __str__(self):
        return "User %s | Name %s | Delivery_date %s" % (self.user.username, self.product.name, self.delivery_date)
