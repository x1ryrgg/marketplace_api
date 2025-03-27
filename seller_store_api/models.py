from django.db import models
from usercontrol_api.models import User


class Store(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=1)
    name = models.CharField(max_length=100, unique=True, null=False, blank=False)
    description = models.CharField(max_length=1000, null=True, blank=True, default="Продавец не оставил описание об магазине.")
    email = models.CharField(max_length=124, null=True, blank=True)
    city = models.CharField(max_length=100, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.email:
            self.email = self.author.email
        super().save(*args, **kwargs)

    def __str__(self):
        return "Author %s | Name %s | city %s" % (self.author, self.name, self.city)



