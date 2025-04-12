from django.apps import AppConfig


class ProductControlApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'product_control_api'

    def ready(self):
        import product_control_api.signals