from django.apps import AppConfig


class UsercontrolApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usercontrol_api'

    def ready(self):
        import usercontrol_api.signals
