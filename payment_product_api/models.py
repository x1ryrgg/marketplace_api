from django.db import models
from usercontrol_api.models import User


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=128, null=False, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    quantity = models.PositiveIntegerField(null=False, blank=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Name %s | Price %s | Quantity %s" % (self.name, self.price, self.quantity)
