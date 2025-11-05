from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import User, StudentProfile


@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    """Auto-create StudentProfile for users with user_type='student'."""
    try:
        is_student = getattr(instance, 'user_type', None) == 'student'
    except Exception:
        is_student = False

    if is_student:
        # ensure profile exists; StudentProfile.save() will populate student_id if needed
        enrollment_date = None
        if hasattr(instance, 'date_joined') and instance.date_joined:
            enrollment_date = instance.date_joined.date()

        StudentProfile.objects.get_or_create(user=instance, defaults={
            'enrollment_date': enrollment_date,
            # 'course' left blank intentionally; admin should assign if known
        })
