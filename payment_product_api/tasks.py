from datetime import date
from .models import Delivery
from usercontrol_api.models import Coupon

from celery import shared_task
from marketplace_api import settings
from marketplace_api.celery import app
from django.core.mail import send_mail


@shared_task
def send_email_task(username, price):
    send_mail(
        subject='Сообщение с marketplace-а',
        message=f'Заказ от пользователя {username} на сумму {price} руб. | {date.today()}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False
    )


@shared_task
def beat_check_delivery():
    today = date.today()
    updated_count = Delivery.objects.filter(
        status='on the way',
        delivery_date=today
    ).update(status='delivered')
    return f"Updated {updated_count} deliveries to 'delivered'."


@shared_task
def beat_check_coupon():
    today = date.today()
    expired_coupon = Coupon.objects.filter(
        end_date=today
    ).delete()
    return f"{expired_coupon} expired coupons removed"