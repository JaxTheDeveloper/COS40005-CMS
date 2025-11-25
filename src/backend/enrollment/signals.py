from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Enrollment, Transcript


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

