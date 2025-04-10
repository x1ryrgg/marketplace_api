import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace_api.settings')

app = Celery('marketplace_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'beat_check_delivery': {
        'task': 'payment_system_api.tasks.beat_check_delivery',
        'schedule': crontab(minute='*/1')
    },
    'beat_check_coupon': {
            'task': 'payment_system_api.tasks.beat_check_coupon',
            'schedule': crontab(hour='*/12', minute=0)
        },
}

# crontab(minute='*/1')  crontab(hour='*/12', minute=0)

