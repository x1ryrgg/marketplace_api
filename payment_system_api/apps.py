from django.apps import AppConfig


class PaymentProductApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payment_system_api'

    def ready(self):
        import payment_system_api.signals
