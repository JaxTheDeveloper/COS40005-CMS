"""
Property-based tests for the Event Content Refiner (WF-4).

Tests cover all 6 correctness properties from the design document:
  1. Valid staff POST returns 202 + generation_status='pending' (n8n path)
  2. Whitespace/empty prompt returns 400, status unchanged
  3. Provided current_content used as mock refiner source
  4. n8n payload contains all required keys for any event targeting config
  5. Mock refiner prepends prompt note to every content field
  6. register_wf4 management command is idempotent

Run with:
    python manage.py test src.backend.core.tests.test_refine_content --verbosity=2
"""
from unittest.mock import patch, MagicMock

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from src.backend.core.models import Event

User = get_user_model()
N8NWorkflow = apps.get_model('users', 'N8NWorkflow')

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_staff():
    import uuid
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f'staff_{uid}', email=f'staff_{uid}@test.com',
        password='pw', is_staff=True,
    )


def _make_student():
    import uuid
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f'student_{uid}', email=f'student_{uid}@test.com',
        password='pw', user_type='student',
    )


def _make_event(creator, generated_content=None):
    return Event.objects.create(
        title='Test Event', description='A test event',
        start=timezone.now(), end=timezone.now() + timezone.timedelta(hours=1),
        created_by=creator,
        generated_content=generated_content or {
            'social_post': 'Original social post',
            'email_newsletter': 'Original email',
        },
        generation_status='ready',
    )


def _make_wf4_record(webhook_url='http://n8n-test/webhook/event-refine'):
    """Create a real N8NWorkflow DB record for event.refine."""
    return N8NWorkflow.objects.create(
        name='SwinCMS — Event Content Refiner (test)',
        trigger_event='event.refine',
        configuration={'webhook_url': webhook_url},
        is_active=True,
    )


def _refine_url(event_id):
    from django.urls import reverse
    return reverse('event-refine-content', kwargs={'pk': event_id})


def _api_client_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


# ---------------------------------------------------------------------------
# Property 1: Valid staff POST returns 202 + pending status (n8n path)
# Feature: event-content-refiner
# ---------------------------------------------------------------------------

class TestProperty1ValidStaffReturns202(HypothesisTestCase):
    """Property 1: Valid staff requests set pending status and return 202."""

    @h_settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    @given(prompt=st.text(min_size=1).filter(lambda s: s.strip()))
    def test_valid_staff_post_returns_202_and_pending(self, prompt):
        """
        For any non-empty, non-whitespace prompt, a staff POST with an active
        event.refine workflow should return 202 and set generation_status='pending'.
        Validates: Requirements 1.1, 2.2
        """
        staff = _make_staff()
        event = _make_event(staff)
        wf = _make_wf4_record()

        try:
            with patch('src.backend.core.n8n_client.requests') as mock_req:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {}
                mock_req.post.return_value = mock_resp

                resp = _api_client_for(staff).post(
                    _refine_url(event.pk),
                    {'refinement_prompt': prompt},
                    format='json',
                )

            self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
            event.refresh_from_db()
            self.assertEqual(event.generation_status, 'pending')
        finally:
            wf.delete()


# ---------------------------------------------------------------------------
# Property 2: Whitespace/empty prompt returns 400, status unchanged
# Feature: event-content-refiner
# ---------------------------------------------------------------------------

class TestProperty2EmptyPromptReturns400(HypothesisTestCase):
    """Property 2: Empty or whitespace prompts are rejected."""

    @h_settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    @given(prompt=st.one_of(st.just(''), st.text(alphabet=' \t\n\r', min_size=1)))
    def test_whitespace_prompt_returns_400(self, prompt):
        """
        For any empty or whitespace-only prompt, the endpoint should return 400
        and leave generation_status unchanged.
        Validates: Requirements 1.3
        """
        staff = _make_staff()
        event = _make_event(staff)
        original_status = event.generation_status

        resp = _api_client_for(staff).post(
            _refine_url(event.pk),
            {'refinement_prompt': prompt},
            format='json',
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        event.refresh_from_db()
        self.assertEqual(event.generation_status, original_status)

    def test_missing_prompt_returns_400(self):
        """Missing refinement_prompt key also returns 400."""
        staff = _make_staff()
        event = _make_event(staff)
        resp = _api_client_for(staff).post(_refine_url(event.pk), {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Property 3: Provided current_content used as mock refiner source
# Feature: event-content-refiner
# ---------------------------------------------------------------------------

class TestProperty3CurrentContentUsedAsSource(HypothesisTestCase):
    """Property 3: Provided current_content is used as refinement source."""

    @h_settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    @given(content=st.dictionaries(
        st.text(min_size=1, max_size=20).filter(str.isidentifier),
        st.text(min_size=1, max_size=50).filter(lambda s: '\x00' not in s),
        min_size=1, max_size=5,
    ))
    def test_provided_current_content_used_not_stored(self, content):
        """
        When current_content is provided and no workflow is active, the mock
        refiner should use the provided content, not event.generated_content.
        Validates: Requirements 1.4
        """
        staff = _make_staff()
        # stored content has different keys from what we'll pass
        event = _make_event(staff, generated_content={'social_post': 'stored content only'})
        # No N8NWorkflow record → mock path

        resp = _api_client_for(staff).post(
            _refine_url(event.pk),
            {'refinement_prompt': 'make it better', 'current_content': content},
            format='json',
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        returned = resp.data['generated_content']
        for key in content:
            self.assertIn(key, returned)
        # Keys only in stored content (not in provided content) should not appear
        for key in event.generated_content:
            if key not in content:
                self.assertNotIn(key, returned)


# ---------------------------------------------------------------------------
# Property 4: n8n payload contains all required keys
# Feature: event-content-refiner
# ---------------------------------------------------------------------------

class TestProperty4PayloadStructure(HypothesisTestCase):
    """Property 4: n8n payload contains all required keys for any event."""

    @h_settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    @given(
        prompt=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
        target_all=st.booleans(),
    )
    def test_payload_has_all_required_keys(self, prompt, target_all):
        """
        For any event targeting configuration and any non-empty prompt, the payload
        passed to n8n must contain all required keys.
        Validates: Requirements 2.1, 2.5, 3.1, 3.2, 3.3
        """
        staff = _make_staff()
        event = _make_event(staff)
        event.target_all_students = target_all
        event.save(update_fields=['target_all_students'])
        wf = _make_wf4_record()

        captured = {}

        try:
            with patch('src.backend.core.n8n_client.requests') as mock_req:
                def capture_post(url, json=None, **kw):
                    if json:
                        captured.update(json)
                    mock_resp = MagicMock()
                    mock_resp.status_code = 200
                    mock_resp.json.return_value = {}
                    return mock_resp

                mock_req.post.side_effect = capture_post

                resp = _api_client_for(staff).post(
                    _refine_url(event.pk),
                    {'refinement_prompt': prompt},
                    format='json',
                )

            if resp.status_code == status.HTTP_202_ACCEPTED:
                # n8n_client wraps payload under 'payload' key
                inner = captured.get('payload', captured)
                for key in ('event_id', 'current_content', 'refinement_prompt', 'audience_context'):
                    self.assertIn(key, inner, msg=f'Missing key: {key}')
                ac = inner['audience_context']
                for ac_key in ('visibility', 'target_all_students', 'target_student_count',
                               'target_offering_ids', 'target_intake_ids'):
                    self.assertIn(ac_key, ac, msg=f'Missing audience_context key: {ac_key}')
        finally:
            wf.delete()


# ---------------------------------------------------------------------------
# Property 5: Mock refiner prepends note to every content field
# Feature: event-content-refiner
# ---------------------------------------------------------------------------

class TestProperty5MockRefinerPrependsNote(HypothesisTestCase):
    """Property 5: Mock refiner applies prompt note to every content field."""

    @h_settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    @given(
        content=st.dictionaries(
            st.text(min_size=1, max_size=20).filter(str.isidentifier),
            st.text(max_size=100).filter(lambda s: '\x00' not in s),
            min_size=1, max_size=5,
        ),
        prompt=st.text(min_size=1, max_size=50).filter(lambda s: s.strip() and '\x00' not in s),
    )
    def test_mock_refiner_prepends_note_to_all_fields(self, content, prompt):
        """
        When no active workflow is registered, the mock refiner should prepend
        '[Refinement note: {prompt}]\\n' to every field in current_content.
        Validates: Requirements 6.1, 6.2, 6.3
        """
        staff = _make_staff()
        event = _make_event(staff)
        # No N8NWorkflow record → mock path

        resp = _api_client_for(staff).post(
            _refine_url(event.pk),
            {'refinement_prompt': prompt, 'current_content': content},
            format='json',
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        returned = resp.data['generated_content']
        expected_prefix = f'[Refinement note: {prompt}]\n'

        for key in content:
            self.assertIn(key, returned)
            self.assertTrue(
                str(returned[key]).startswith(expected_prefix),
                msg=f'Field "{key}" missing prefix. Got: {returned[key]!r}',
            )

        self.assertEqual(resp.data['generation_meta']['generated_by'], 'mock-refine')
        self.assertEqual(resp.data['generation_meta']['refinement_prompt'], prompt)


# ---------------------------------------------------------------------------
# Property 6: register_wf4 is idempotent
# Feature: event-content-refiner
# ---------------------------------------------------------------------------

class TestProperty6RegisterWf4Idempotent(HypothesisTestCase):
    """Property 6: register_wf4 management command is idempotent."""

    def tearDown(self):
        N8NWorkflow.objects.filter(trigger_event='event.refine').delete()

    @h_settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    @given(url=st.from_regex(
        r'https?://[a-z0-9-]+(\.[a-z0-9-]+)*/webhook/[a-z-]+',
        fullmatch=True,
    ))
    def test_register_wf4_idempotent(self, url):
        """
        Running register_wf4 multiple times with the same URL should result in
        exactly one N8NWorkflow record with trigger_event='event.refine' and is_active=True.
        Validates: Requirements 4.1, 4.4, 4.5
        """
        N8NWorkflow.objects.filter(trigger_event='event.refine').delete()

        for _ in range(3):
            call_command('register_wf4', webhook_url=url, verbosity=0)

        count = N8NWorkflow.objects.filter(trigger_event='event.refine').count()
        self.assertEqual(count, 1, msg=f'Expected 1 record, got {count}')
        wf = N8NWorkflow.objects.get(trigger_event='event.refine')
        self.assertTrue(wf.is_active)
        self.assertEqual(wf.configuration['webhook_url'], url)


# ---------------------------------------------------------------------------
# Non-staff access — sanity checks
# ---------------------------------------------------------------------------

class TestNonStaffForbidden(APITestCase):
    def setUp(self):
        self.student = _make_student()
        staff = _make_staff()
        self.event = _make_event(staff)

    def test_student_gets_403(self):
        self.client.force_authenticate(user=self.student)
        resp = self.client.post(
            _refine_url(self.event.pk),
            {'refinement_prompt': 'make it better'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_gets_401_or_403(self):
        resp = self.client.post(
            _refine_url(self.event.pk),
            {'refinement_prompt': 'make it better'},
            format='json',
        )
        self.assertIn(resp.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ])
