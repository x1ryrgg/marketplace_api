import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    def __str__(self):
        return 'username: %s | email: %s | pk %s' % (self.username, self.email, self.pk)


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='media/images/%Y/%m/%d/', blank=True)
    date_of_birth = models.DateField(blank=True, null=True, default=datetime.date.today)

    def __str__(self):
        return "profile of user %s" % self.user.username
