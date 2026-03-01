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
    """Notify student when enrollment becomes active or withdrawn."""
    new_status = instance.status
    old_status = getattr(instance, '_old_status', None)

    should_notify = False
    if created and new_status in ['ENROLLED', 'WITHDRAWN']:
        should_notify = True
    if not created and new_status != old_status and new_status in ['ENROLLED', 'WITHDRAWN']:
        should_notify = True

    if not should_notify:
        return

    verb = f"Enrollment {new_status.lower()}"
    Notification.objects.create(
        recipient=instance.student,
        verb=verb,
        target_content_type=ContentType.objects.get_for_model(instance),
        target_object_id=instance.pk,
    )

