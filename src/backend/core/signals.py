"""
core/signals.py — Outbound n8n triggers for attendance events.

When an AttendanceRecord is saved with status='present', all active n8n workflows
registered with trigger_event='attendance.marked' are called in a background thread.
"""

import threading
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import AttendanceRecord

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Background dispatcher (runs in a daemon thread so it never blocks the request)
# ---------------------------------------------------------------------------

def _dispatch_n8n_attendance(instance_pk):
    """
    Fire attendance.marked n8n workflows.
    Fetches a fresh copy of the record to avoid lazy-load issues across threads.
    """
    try:
        from django.apps import apps
        N8NWorkflow = apps.get_model('users', 'N8NWorkflow')
        N8NExecutionLog = apps.get_model('users', 'N8NExecutionLog')
        from src.backend.core.n8n_client import trigger_workflow

        workflows = N8NWorkflow.objects.filter(
            trigger_event='attendance.marked', is_active=True
        )
        if not workflows.exists():
            return

        # Fetch fresh instance (avoid cross-thread model state issues)
        record = AttendanceRecord.objects.select_related(
            'student', 'session', 'session__unit', 'session__offering'
        ).get(pk=instance_pk)

        session = record.session

        payload = {
            'student_id': record.student_id,
            'student_email': record.student.email,
            'student_name': record.student.get_full_name(),
            'attendance_status': record.status,
            'session_id': session.id,
            'offering_id': session.offering_id,
            'unit_code': session.unit.code,
            'unit_name': session.unit.name,
            'event_date': session.date.isoformat(),
        }

        for wf in workflows:
            log = N8NExecutionLog.objects.create(
                workflow=wf,
                triggered_by=None,
                start_time=timezone.now(),
                status='running',
                input_data=payload,
            )
            try:
                sc, resp = trigger_workflow(wf, record.pk, payload)
                log.status = 'completed' if 200 <= sc < 300 else 'failed'
                log.output_data = {'status_code': sc, 'response': resp}
            except Exception as exc:
                log.status = 'failed'
                log.error_details = {'error': str(exc)}
            finally:
                log.end_time = timezone.now()
                log.save()

    except Exception:
        logger.exception('_dispatch_n8n_attendance error for pk=%s', instance_pk)


# ---------------------------------------------------------------------------
# Signal handler
# ---------------------------------------------------------------------------

@receiver(post_save, sender=AttendanceRecord)
def attendance_post_save(sender, instance, **kwargs):
    """
    After an attendance record is saved, if status is 'present' fire any
    registered n8n workflows for attendance.marked in a background thread.
    """
    if instance.status == 'present':
        threading.Thread(
            target=_dispatch_n8n_attendance,
            args=(instance.pk,),
            daemon=True,
        ).start()
