from django.core.mail import send_mail
from django.core.management import BaseCommand
from marketplace_api import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class Command(BaseCommand):
    help = 'send complex email message'

    def handle(self, *args, **options):
        self.stdout.write('Send message')

        name = 'Dear User'
        subject = f'Сообщение для {name}!'

        context = {
            "name": name
        }
        text_content = render_to_string(
            "email_message/email_message.txt",
            context=context,
        )
        html_content = render_to_string(
            "email_message/email_message.html",
            context=context,
        )

        sender = settings.EMAIL_HOST_USER
        recipient = [settings.EMAIL_HOST_USER]
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=sender,
            to=recipient,
            headers={"List-Unsubscribe": "<mailto:unsub@example.com>"},
        )

        msg.attach_alternative(html_content, "text/html")
        msg.send()

        self.stdout.write(self.style.SUCCESS('Complex email sent'))
