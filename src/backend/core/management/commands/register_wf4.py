"""
Management command to register or update the WF-4 n8n workflow record.

Usage:
    # Default internal URL (use when n8n workflow is Activated)
    python manage.py register_wf4

    # Set the production (internal) webhook URL
    python manage.py register_wf4 --webhook-url http://cos40005_n8n:5678/webhook/event-refine

    # Set the ngrok test URL (webhook-test path, used while building in n8n)
    python manage.py register_wf4 --test-url https://<your-ngrok>.ngrok-free.app/webhook-test/<uuid>

    # Switch active URL to test mode (uses webhook_url_test)
    python manage.py register_wf4 --use-test

    # Switch active URL back to production mode (uses webhook_url)
    python manage.py register_wf4 --use-prod

    # Set both URLs and activate test mode in one command
    python manage.py register_wf4 \\
        --webhook-url http://cos40005_n8n:5678/webhook/event-refine \\
        --test-url https://<your-ngrok>.ngrok-free.app/webhook-test/<uuid> \\
        --use-test
"""
from django.core.management.base import BaseCommand
from django.apps import apps

DEFAULT_WEBHOOK_URL = 'http://cos40005_n8n:5678/webhook/event-refine'


class Command(BaseCommand):
    help = 'Register or update the WF-4 event.refine N8NWorkflow record'

    def add_arguments(self, parser):
        parser.add_argument(
            '--webhook-url',
            default=None,
            help=f'Production/internal webhook URL (default: {DEFAULT_WEBHOOK_URL})',
        )
        parser.add_argument(
            '--test-url',
            default=None,
            help='ngrok/test webhook-test URL for use while building in n8n',
        )
        # Mutually exclusive toggle flags
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            '--use-test',
            action='store_true',
            default=False,
            help='Switch active URL to test mode (uses webhook_url_test)',
        )
        mode.add_argument(
            '--use-prod',
            action='store_true',
            default=False,
            help='Switch active URL to production mode (uses webhook_url)',
        )

    def handle(self, *args, **options):
        N8NWorkflow = apps.get_model('users', 'N8NWorkflow')

        wf, created = N8NWorkflow.objects.get_or_create(
            trigger_event='event.refine',
            defaults={
                'name': 'SwinCMS — Event Content Refiner',
                'description': (
                    'WF-4: Receives a refinement prompt + current content from Django, '
                    'calls Groq to refine, POSTs result back via generation_callback.'
                ),
                'configuration': {},
                'is_active': True,
            },
        )

        config = wf.configuration or {}
        old_url = config.get('webhook_url', '<not set>')
        old_test_url = config.get('webhook_url_test', '<not set>')
        old_mode = 'test' if config.get('use_test_url') else 'prod'

        if created:
            self.stdout.write(f'Created new N8NWorkflow for event.refine')
        else:
            self.stdout.write(f'Found existing N8NWorkflow: {wf.name} (id={wf.pk})')
            self.stdout.write(f'  webhook_url      : {old_url}')
            self.stdout.write(f'  webhook_url_test : {old_test_url}')
            self.stdout.write(f'  active mode      : {old_mode}')

        # Update URLs if provided
        if options['webhook_url']:
            config['webhook_url'] = options['webhook_url']
        elif 'webhook_url' not in config:
            config['webhook_url'] = DEFAULT_WEBHOOK_URL

        if options['test_url']:
            config['webhook_url_test'] = options['test_url']

        # Toggle active mode
        if options['use_test']:
            if not config.get('webhook_url_test'):
                self.stderr.write(self.style.ERROR(
                    'Cannot switch to test mode: webhook_url_test is not set. '
                    'Provide --test-url first.'
                ))
                return
            config['use_test_url'] = True
        elif options['use_prod']:
            config['use_test_url'] = False

        config.setdefault('use_test_url', False)
        config.setdefault('notes', (
            'Toggle between test and prod URLs with:\n'
            '  python manage.py register_wf4 --use-test\n'
            '  python manage.py register_wf4 --use-prod'
        ))

        wf.name = 'SwinCMS — Event Content Refiner'
        wf.configuration = config
        wf.is_active = True
        wf.save()

        active_mode = 'TEST' if config.get('use_test_url') else 'PROD'
        active_url = config.get('webhook_url_test') if config.get('use_test_url') else config.get('webhook_url')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Active mode    : {active_mode}'))
        self.stdout.write(self.style.SUCCESS(f'Active URL     : {active_url}'))
        self.stdout.write(self.style.SUCCESS('Done.'))
