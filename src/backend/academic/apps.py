from django.apps import AppConfig


class AcademicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.backend.academic'
    verbose_name = 'Academic Management'