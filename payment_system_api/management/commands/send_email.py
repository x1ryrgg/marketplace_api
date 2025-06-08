from django.core.mail import send_mail
from django.core.management import BaseCommand
from marketplace_api import settings


class Command(BaseCommand):
    help = 'send email message'

    def handle(self, *args, **options):
        self.stdout.write('Send message')

        send_mail(
            subject='Сообщение',
            message='Это тестовое сообщение',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False
        )
        self.stdout.write(self.style.SUCCESS('Email sent'))