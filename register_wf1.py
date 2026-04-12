"""Update N8NWorkflow webhook_url to ngrok test URL for active testing."""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from src.backend.users.models import N8NWorkflow

wf = N8NWorkflow.objects.filter(trigger_event='event.generate').first()
if not wf:
    print("ERROR: N8NWorkflow for event.generate not found")
    import sys; sys.exit(1)

print(f"Current webhook_url: {wf.configuration.get('webhook_url')}")

# Use the ngrok test URL while the workflow is being built/tested in n8n
# Switch back to internal URL once the workflow is activated in n8n
ngrok_test = 'https://conditionally-brimful-exie.ngrok-free.dev/webhook-test/0ecfdf01-3840-4d68-9ac0-800489620a54'
ngrok_prod  = 'https://conditionally-brimful-exie.ngrok-free.dev/webhook/0ecfdf01-3840-4d68-9ac0-800489620a54'
internal    = 'http://cos40005_n8n:5678/webhook/0ecfdf01-3840-4d68-9ac0-800489620a54'

config = wf.configuration or {}
config['webhook_url']      = ngrok_test   # <-- test mode while building
config['webhook_url_prod'] = ngrok_prod
config['webhook_url_internal'] = internal
config['notes'] = (
    'Currently using ngrok-test URL while n8n workflow is in test mode. '
    'Switch webhook_url to webhook_url_internal once workflow is Activated in n8n.'
)
wf.configuration = config
wf.is_active = True
wf.save()

print(f"Updated webhook_url to: {wf.configuration['webhook_url']}")
print("Done.")
