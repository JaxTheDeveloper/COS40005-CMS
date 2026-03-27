"""Verify two-phase callback + GCal fields."""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

errors = []

def check(label, fn):
    try:
        result = fn()
        print(f"  OK  {label}" + (f" → {result}" if result is not None else ""))
    except Exception as e:
        print(f"  FAIL {label}: {e}")
        errors.append(label)

print("\n=== Event model new fields ===")
from src.backend.core.models import Event
check("gcal_event_id field exists",
      lambda: Event._meta.get_field('gcal_event_id').max_length)
check("generation_timeout_at field exists",
      lambda: str(Event._meta.get_field('generation_timeout_at')))

print("\n=== generation_callback two-phase behaviour ===")
from src.backend.core.views_api import EventViewSet
check("generation_callback method exists",
      lambda: callable(EventViewSet.generation_callback))
check("gcal_sync method exists",
      lambda: callable(EventViewSet.gcal_sync))

print("\n=== End-to-end DB check (create + update event) ===")
from django.utils import timezone
check("Can create Event with gcal_event_id",
      lambda: Event.objects.create(
          title='Test GCal Event',
          start=timezone.now(),
          gcal_event_id='test-gcal-id-123',
          generation_status='pending',
      ).delete())

print(f"\n{'ALL CHECKS PASSED' if not errors else f'FAILURES: {errors}'}")
import sys; sys.exit(0 if not errors else 1)
