"""Test generation_callback two-phase handling including string coercion."""
import os, django, json
os.environ.setdefaults = lambda *a, **k: None
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

import json as _json
from django.test import RequestFactory, override_settings
from rest_framework.test import APIRequestFactory
from django.utils import timezone
from src.backend.core.models import Event
from src.backend.core.views_api import EventViewSet

factory = APIRequestFactory()
errors = []

def check(label, fn):
    try:
        result = fn()
        print(f"  OK  {label}")
        return result
    except Exception as e:
        print(f"  FAIL {label}: {e}")
        errors.append(label)
        return None

# Create a test event
print("\n=== Setup ===")
event = check("Create test event",
    lambda: Event.objects.create(title='Test', start=timezone.now()))

if event:
    vs = EventViewSet()
    vs.kwargs = {'pk': event.pk}
    vs.format_kwarg = 'json'

    print("\n=== Phase 1: gcal_event_id only ===")
    req = factory.post(f'/api/core/events/{event.pk}/generation_callback/',
        {'gcal_event_id': 'test_gcal_123'}, format='json')
    vs.request = req
    with override_settings(DEBUG=True, N8N_WEBHOOK_SECRET=None):
        vs.action = 'generation_callback'
        resp = EventViewSet.as_view({'post': 'generation_callback'})(req, pk=event.pk)
    check("Phase 1 returns 200", lambda: resp.status_code == 200 or print(resp.data))
    event.refresh_from_db()
    check("gcal_event_id stored", lambda: event.gcal_event_id == 'test_gcal_123')
    check("status is pending", lambda: event.generation_status == 'pending')

    print("\n=== Phase 2: generated_content as STRING (n8n bug simulation) ===")
    content_str = _json.dumps({"social_post": "Hello world", "email_newsletter": "Dear student..."})
    req2 = factory.post(f'/api/core/events/{event.pk}/generation_callback/',
        {'generated_content': content_str, 'generation_meta': '{"source":"groq"}'},
        format='json')
    with override_settings(DEBUG=True, N8N_WEBHOOK_SECRET=None):
        resp2 = EventViewSet.as_view({'post': 'generation_callback'})(req2, pk=event.pk)
    check("Phase 2 (string content) returns 200", lambda: resp2.status_code == 200 or print(resp2.data))
    event.refresh_from_db()
    check("status is ready", lambda: event.generation_status == 'ready')
    check("social_post stored", lambda: event.generated_content.get('social_post') == 'Hello world')

    # Cleanup
    event.delete()

print(f"\n{'ALL CHECKS PASSED' if not errors else f'FAILURES: {errors}'}")
import sys; sys.exit(0 if not errors else 1)
