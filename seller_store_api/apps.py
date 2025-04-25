from django.apps import AppConfig


class SellerStoreApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'seller_store_api'

    def ready(self):
        import seller_store_api.signals
