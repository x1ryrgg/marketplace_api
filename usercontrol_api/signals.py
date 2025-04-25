import os
import logging

from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch import receiver
from .models import Profile, WishlistItem, Notification

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Profile)
def delete_old_image_on_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Profile.objects.get(pk=instance.pk)
            if old_instance.image and old_instance.image != instance.image:
                if os.path.exists(old_instance.image.path):
                    os.remove(old_instance.image.path)
                    logger.info(f"Old image {old_instance.image.url} deleted")
        except Profile.DoesNotExist:
            pass


@receiver(pre_delete, sender=Profile)
def delete_profile_image(sender, instance, **kwargs):
    if instance.image:
        logger.debug(f"Image path: {instance.image.path}")
        if os.path.exists(instance.image.path):
            os.remove(instance.image.path)
            logger.info(f"Image {instance.image.url} deleted")
        else:
            logger.warning(f"Image file does not exist: {instance.image.url}")


@receiver(post_save, sender=WishlistItem)
def wishlist_notification(sender, instance, created, **kwargs):
    added_quantity = getattr(instance, 'added_quantity', 1)

    Notification.objects.create(
        user=instance.user,
        title=Notification.TitleChoice.OTHER,
        message=f"{instance.product.product.name} ({added_quantity} шт) добавлен в список желаемого."
    )