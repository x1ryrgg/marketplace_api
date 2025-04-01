import datetime
import os
import logging

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class User(AbstractUser):
    is_seller = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    wishlist = models.ManyToManyField('seller_store_api.Product', through='usercontrol_api.WishlistItem', blank=True)

    def __str__(self):
        return 'username: %s | email: %s | pk %s' % (self.username, self.email, self.pk)


class WishlistItem(models.Model):
    user = models.ForeignKey('usercontrol_api.User', on_delete=models.CASCADE)
    product = models.ForeignKey('seller_store_api.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('user', 'product')


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True, default=datetime.date.today)

    def __str__(self):
        return "profile of user %s" % self.user.username


