from datetime import date, timedelta
from .models import Delivery
from usercontrol_api.models import Coupon, Notification

from celery import shared_task
from marketplace_api import settings
from marketplace_api.celery import app
from django.core.mail import send_mail


@shared_task
def send_email_task(username, price):
    message = send_mail(
        subject='Сообщение с marketplace-а',
        message=f'Заказ от пользователя {username} на сумму {price} руб. | {date.today()}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False
    )
    return message

@shared_task
def beat_check_delivery():
    today = date.today()

    deliveries = Delivery.objects.filter(
        status='on the way',
        delivery_date__lte=today
    ).select_related('user', 'product', 'product__product')  # Оптимизация запросов

    delivery_ids = list(deliveries.values_list('id', flat=True))

    updated_count = Delivery.objects.filter(id__in=delivery_ids).update(status='delivered')

    for delivery in Delivery.objects.filter(id__in=delivery_ids).select_related('user', 'product', 'product__product'):

        Notification.objects.create(
            user=delivery.user,
            title=Notification.TitleChoice.DELIVERY,
            message=f"Товар {getattr(delivery.product.product, 'name', '№' + str(delivery.id))} доставлен"
        )

    return f"Обновлено: {updated_count} доставок. "


@shared_task
def beat_check_coupon():
    today = date.today()
    expired_coupon = Coupon.objects.filter(
        end_date__lte=today
    ).delete()
    return f"{expired_coupon[0]} купонов удаленно. "


@shared_task
def beat_check_read_notification():
    data = date.today() - timedelta(days=7)

    expired_notifications = Notification.objects.filter(
        created_at__lte=data,
        is_read=True
    ).delete()

    return f"Прочитанных уведомлений удаленно: {expired_notifications[0]}"


@shared_task
def beat_check_notification():
    data = date.today() - timedelta(days=30)

    expired_notifications = Notification.objects.filter(
        created_at__lte=data,
        is_read=False
    ).delete()

    return f"Уведомлений удаленно: {expired_notifications[0]}"