from django.apps import AppConfig

class MisenServerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mixen"

    def ready(self):
        # Import signals so they are registered
        import mixen.signals
