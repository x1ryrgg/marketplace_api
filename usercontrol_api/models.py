import datetime
import os
import logging
import random

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_seller = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    wishlist = models.ManyToManyField('product_control_api.Product', through='usercontrol_api.WishlistItem', blank=True)

    def __str__(self):
        return 'username: %s | pk %s)' % (self.username, self.pk)


class WishlistItem(models.Model):
    user = models.ForeignKey('usercontrol_api.User', on_delete=models.CASCADE)
    product = models.ForeignKey('product_control_api.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('user', 'product')


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True, default=datetime.date.today)

    def __str__(self):
        return "profile of user %s" % self.user.username


class Coupon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.PositiveIntegerField(blank=True, null=True)
    discount = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return "Coupon owner %s | code %s | end_date %s" % (self.user, self.code, self.end_date)

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
        if not self.code:
            self.code = random.randint(100000, 999999)
        if not self.discount:
            self.discount = random.randint(5, 40)
        if not self.end_date:
            self.end_date = self.created_at + datetime.timedelta(weeks=4)
        super().save(update_fields=['code', 'discount', 'end_date'])

