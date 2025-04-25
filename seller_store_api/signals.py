import os
import logging

from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch import receiver

from usercontrol_api.models import Notification
from .models import Review, Store


logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Review)
def delete_old_image_on_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Review.objects.get(pk=instance.pk)
            if old_instance.image and old_instance.image != instance.image:
                if os.path.exists(old_instance.image.path):
                    os.remove(old_instance.image.path)
                    logger.info(f"Old image {old_instance.image.url} deleted")
        except Review.esNotExist:
            pass


@receiver(pre_delete, sender=Review)
def delete_review_image(sender, instance, **kwargs):
    if instance.image:
        logger.debug(f"Image path: {instance.image.path}")
        if os.path.exists(instance.image.path):
            os.remove(instance.image.path)
            logger.info(f"Image {instance.image.url} deleted")
        else:
            logger.warning(f"Image file does not exist: {instance.image.url}")


@receiver(post_save, sender=Store)
def store_create_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.author,
            title=Notification.TitleChoice.CELLER,
            message=f"{instance.name} зарегестирован на вас ({instance.author.username})"
        )