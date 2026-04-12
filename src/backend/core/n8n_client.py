import logging
from django.conf import settings
from django.db.models import F
from django.utils import timezone
import requests

logger = logging.getLogger(__name__)


def _resolve_webhook_url(config: dict) -> str:
    """
    Pick the right webhook URL from a workflow's configuration dict.

    Resolution order:
      1. If ``use_test_url`` is True  → use ``webhook_url_test``
      2. Otherwise                    → use ``webhook_url`` (production / internal)

    Set ``use_test_url`` via the management command:
        python manage.py register_wf4 --use-test      # switch to test URL
        python manage.py register_wf4 --use-prod      # switch back to prod URL
    """
    use_test = config.get('use_test_url', False)

    if use_test:
        url = config.get('webhook_url_test') or config.get('webhook_url')
    else:
        url = config.get('webhook_url') or config.get('trigger_url')

    if not url:
        raise ValueError('workflow.configuration.webhook_url missing')
    return url


def trigger_workflow(workflow, event_id, payload):
    """Trigger an n8n workflow using a webhook URL stored on the workflow.configuration.

    - workflow: N8NWorkflow instance (expected to have `configuration` JSON with `webhook_url`)
    - event_id: id of the Django Event being processed
    - payload: dict payload to POST to the workflow

    The active URL is chosen by ``_resolve_webhook_url``:
      - ``use_test_url: true``  in configuration → uses ``webhook_url_test``
      - ``use_test_url: false`` (default)         → uses ``webhook_url``

    Returns: (status_code, response_json or text)
    """
    config = getattr(workflow, 'configuration', {}) or {}
    webhook_url = _resolve_webhook_url(config)

    headers = {
        'Content-Type': 'application/json',
    }

    # Prefer an API key from Django settings. Do NOT hardcode secrets in code.
    api_key = getattr(settings, 'N8N_API_KEY', None)
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
        headers['X-N8N-API-KEY'] = api_key

    json_payload = {
        'event_id': str(event_id),
        'timestamp': timezone.now().isoformat(),
        'payload': payload,
    }

    logger.debug(
        'Triggering workflow %s → %s (test=%s)',
        workflow, webhook_url, config.get('use_test_url', False),
    )

    try:
        resp = requests.post(webhook_url, json=json_payload, headers=headers, timeout=30)
        try:
            data = resp.json()
        except Exception:
            data = resp.text

        # Update last_run on success
        workflow.last_run = timezone.now()
        workflow.save(update_fields=['last_run'])

        return resp.status_code, data
    except Exception as exc:
        logger.exception('Error triggering n8n workflow %s', workflow)
        # Increment error_count on failure
        workflow.error_count = F('error_count') + 1
        workflow.save(update_fields=['error_count'])
        raise
