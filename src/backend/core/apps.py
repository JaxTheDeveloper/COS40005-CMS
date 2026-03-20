from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.backend.core'
    verbose_name = 'Core'

    def ready(self):
        import src.backend.core.signals  # noqa — registers attendance signal handlers
