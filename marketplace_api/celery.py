import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace_api.settings')

app = Celery('marketplace_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'beat_check_delivery': {
        'task': 'payment_product_api.tasks.beat_check_delivery',
        'schedule': crontab(hour='*/12', minute=0)
    },
}
