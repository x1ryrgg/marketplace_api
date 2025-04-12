from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ProductVariant


@receiver(pre_save, sender=ProductVariant)
def set_default_values(sender, instance, **kwargs):
    if not instance.quantity:
        instance.quantity = instance.product.quantity
    if not instance.price:
        instance.price = instance.product.price