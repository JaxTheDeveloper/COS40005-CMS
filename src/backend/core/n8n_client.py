import logging
from django.conf import settings
from django.utils import timezone
import requests

logger = logging.getLogger(__name__)


def trigger_workflow(workflow, event_id, payload):
    """Trigger an n8n workflow using a webhook URL stored on the workflow.configuration.

    - workflow: N8NWorkflow instance (expected to have `configuration` JSON with `webhook_url`)
    - event_id: id of the Django Event being processed
    - payload: dict payload to POST to the workflow

    Returns: (status_code, response_json or text)
    """
    config = getattr(workflow, 'configuration', {}) or {}
    webhook_url = config.get('webhook_url') or config.get('trigger_url')
    if not webhook_url:
        raise ValueError('workflow.configuration.webhook_url missing')

    headers = {
        'Content-Type': 'application/json',
    }

    # Prefer an API key from Django settings. Do NOT hardcode secrets in code.
    api_key = getattr(settings, 'N8N_API_KEY', None)
    if api_key:
        # Try common header forms
        headers['Authorization'] = f'Bearer {api_key}'
        headers['X-N8N-API-KEY'] = api_key

    json_payload = {
        'event_id': str(event_id),
        'timestamp': timezone.now().isoformat(),
        'payload': payload,
    }

    try:
        resp = requests.post(webhook_url, json=json_payload, headers=headers, timeout=30)
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        return resp.status_code, data
    except Exception as exc:
        logger.exception('Error triggering n8n workflow %s', workflow)
        raise
