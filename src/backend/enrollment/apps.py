from django.apps import AppConfig


class EnrollmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.backend.enrollment'
    verbose_name = 'Course Enrollment'