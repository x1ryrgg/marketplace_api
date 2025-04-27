from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .models import Delivery
from product_control_api.models import ProductVariant
from usercontrol_api.models import Notification


""" delivery notification """
@receiver(post_save, sender=Delivery)
def delivery_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.user,
            title=Notification.TitleChoice.DELIVERY,
            message=_(f"Доставка товара {instance.product.product.name} ({instance.quantity} шт). ")
        )