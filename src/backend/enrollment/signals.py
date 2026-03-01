from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import Enrollment, Transcript
from src.backend.core.models import Notification


@receiver(post_save, sender=Enrollment)
def create_or_update_transcript(sender, instance, created, **kwargs):
    """
    Automatically create or update transcript entry when enrollment status changes
    to COMPLETED or FAILED
    """
    # Only create transcript for completed or failed enrollments
    if instance.status in ['COMPLETED', 'FAILED']:
        transcript, created = Transcript.objects.get_or_create(
            enrollment=instance,
            defaults={
                'student': instance.student,
                'unit_code': instance.offering.unit.code,
                'unit_name': instance.offering.unit.name,
                'semester': instance.offering.semester,
                'year': instance.offering.year,
                'credit_points': instance.offering.unit.credit_points,
                'grade': instance.grade,
                'marks': instance.marks,
                'status': instance.status,
                'completion_date': instance.completion_date or instance.updated_at,
            }
        )
        
        # Update existing transcript if enrollment was updated
        if not created:
            transcript.unit_code = instance.offering.unit.code
            transcript.unit_name = instance.offering.unit.name
            transcript.semester = instance.offering.semester
            transcript.year = instance.offering.year
            transcript.credit_points = instance.offering.unit.credit_points
            transcript.grade = instance.grade
            transcript.marks = instance.marks
            transcript.status = instance.status
            transcript.completion_date = instance.completion_date or instance.updated_at
            transcript.save()
    
    # Delete transcript if enrollment is withdrawn (optional - you may want to keep historical records)
    elif instance.status == 'WITHDRAWN':
        Transcript.objects.filter(enrollment=instance).delete()


# ---------------------------------------------------------------------------
# Enrollment notifications
# ---------------------------------------------------------------------------

@receiver(pre_save, sender=Enrollment)
def enrollment_pre_save(sender, instance, **kwargs):
    """Capture previous status before it changes."""
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Enrollment)
def enrollment_post_save(sender, instance, created, **kwargs):
    """Notify students and staff about relevant status changes.

    * When a record is created with status PENDING, send a notification to the
      responsible staff/convenor so they know an approval is required.
    * When the status later flips to ENROLLED or WITHDRAWN, notify the student.
    """
    new_status = instance.status
    old_status = getattr(instance, '_old_status', None)

    # first handle newly-created pending enrollments
    if created and new_status == 'PENDING':
        # determine recipients: unit convenor plus all staff users
        from django.contrib.auth import get_user_model
        User = get_user_model()

        recipients = set(User.objects.filter(is_staff=True))
        convenor = None
        try:
            convenor = instance.offering.unit.convenor
        except Exception:
            convenor = None
        if convenor:
            recipients.add(convenor)

        for r in recipients:
            Notification.objects.create(
                recipient=r,
                verb='Enrollment pending approval',
                target_content_type=ContentType.objects.get_for_model(instance),
                target_object_id=instance.pk,
            )
        # continue on to student notifications if appropriate

    # then handle student-facing notifications (approve/withdrawn)
    should_notify_student = False
    if created and new_status in ['ENROLLED', 'WITHDRAWN']:
        should_notify_student = True
    if not created and new_status != old_status and new_status in ['ENROLLED', 'WITHDRAWN']:
        should_notify_student = True

    if should_notify_student:
        verb = f"Enrollment {new_status.lower()}"
        Notification.objects.create(
            recipient=instance.student,
            verb=verb,
            target_content_type=ContentType.objects.get_for_model(instance),
            target_object_id=instance.pk,
        )

