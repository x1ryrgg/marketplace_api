from datetime import date
from .models import Delivery

from celery import shared_task
from marketplace_api import settings
from marketplace_api.celery import app
from django.core.mail import send_mail


@shared_task
def send_email_task(username, email):
    send_mail(
        subject='Сообщение с marketplace-а',
        message=f'сообщение от {username}, почта: {email}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False
    )

@shared_task
def beat_check_delivery():
    today = date.today()
    deliveries_to_update = Delivery.objects.filter(
        status='on the way',
        delivery_date=today
    )
    for delivery in deliveries_to_update:
        delivery.status = 'delivered'
        delivery.save(update_fields=['status'])
    return f"Updated {deliveries_to_update.count()} deliveries to 'delivered'."