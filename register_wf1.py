import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from src.backend.users.models import N8NWorkflow

# Internal Docker URL — used when Django inside Docker calls n8n inside Docker
INTERNAL_URL = 'http://cos40005_n8n:5678/webhook/0ecfdf01-3840-4d68-9ac0-800489620a54'

# Ngrok test URL — for external testing / Postman (update with production path when workflow is activated)
NGROK_TEST_URL = 'https://conditionally-brimful-exie.ngrok-free.dev/webhook-test/0ecfdf01-3840-4d68-9ac0-800489620a54'

wf, created = N8NWorkflow.objects.update_or_create(
    trigger_event='event.generate',
    defaults={
        'name': 'SwinCMS - Event Content Generator',
        'description': (
            'Generates AI content (social post, newsletter, recruitment ad, Vietnamese version) '
            'for an event via Groq, then POSTs back via generation_callback (Phase 2) '
            'and syncs the Google Calendar event ID (Phase 1 via gcal-sync).'
        ),
        'is_active': True,
        'configuration': {
            'webhook_url': INTERNAL_URL,
            'ngrok_test_url': NGROK_TEST_URL,
            'webhook_id': '0ecfdf01-3840-4d68-9ac0-800489620a54',
            'notes': 'Switch webhook_url to internal Docker URL when n8n workflow is activated (remove -test from path).',
        },
    }
)

print(f"{'Created' if created else 'Updated'}: {wf.name}")
print(f"  ID:            {wf.pk}")
print(f"  trigger_event: {wf.trigger_event}")
print(f"  is_active:     {wf.is_active}")
print(f"  webhook_url:   {wf.configuration['webhook_url']}")
print(f"  ngrok_test:    {wf.configuration['ngrok_test_url']}")
