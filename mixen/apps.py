from django.apps import AppConfig


class MisenServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mixen'


from django.apps import AppConfig

class MisenServerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mixen"

    def ready(self):
        import mixen.models   # ensures signals load
