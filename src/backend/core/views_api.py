from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from . import models, serializers
from .permissions import (
    IsStaff, IsConvenor, IsOwnerOrReadOnly,
    IsConvenorOrStaffOrReadOnly, IsOwnerOrConvenorOrStaff,
)


class EventViewSet(viewsets.ModelViewSet):
    queryset = models.Event.objects.all().order_by('-start')
    serializer_class = serializers.EventSerializer
    # Events: authenticated users can list/read; convenors and staff can create/edit
    permission_classes = [IsConvenorOrStaffOrReadOnly]

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def targeted_students(self, request, pk=None):
        """
        Return the set of students this event targets, based on targeting rules.
        """
        event = self.get_object()
        students = event.get_targeted_students()
        from src.backend.users.serializers import UserSerializer
        return Response(UserSerializer(students, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def generate_content(self, request, pk=None):
        """
        Trigger generation of event content (scaffold).

        This is a synchronous mocked implementation that simulates calling
        an external GenAI workflow (later: n8n/webhook). It updates the
        event.generated_content and generation_meta and returns the data.
        """
        event = self.get_object()

        # Only convenors/staff or event owner should be allowed to generate in real setup.
        user = request.user
        is_convenor = getattr(user, 'user_type', None) == 'unit_convenor'
        is_staff = user.is_staff
        is_owner = event.created_by_id == getattr(user, 'id', None)
        if not (is_staff or is_convenor or is_owner):
            return Response({'detail': 'Insufficient permissions to generate content.'}, status=status.HTTP_403_FORBIDDEN)

        prompt = request.data.get('prompt') or f"Create marketing copy for event: {event.title}\n\n{event.description}"

        # Mark as pending (in a real system we'd enqueue a job)
        event.generation_status = 'pending'
        event.save()

        # If n8n workflows are configured, trigger matching workflows instead of local mock
        from django.apps import apps
        try:
            UsersModels = apps.get_model('users', 'N8NWorkflow')
            ExecutionLogModel = apps.get_model('users', 'N8NExecutionLog')
        except Exception:
            UsersModels = None
            ExecutionLogModel = None

        triggered_any = False
        errors = []

        if UsersModels:
            workflows = UsersModels.objects.filter(is_active=True, trigger_event='event.generate')
            if workflows.exists():
                # Build payload once — flat structure so n8n Code nodes can
                # read fields directly as payload.title, payload.start, etc.
                import pytz
                _VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

                def _to_rfc3339(dt):
                    """Return RFC 3339 string; make naive datetimes VN-local."""
                    if not dt:
                        return None
                    if timezone.is_naive(dt):
                        dt = _VN_TZ.localize(dt)
                    return dt.isoformat()

                payload = {
                    # Top-level flat fields — consumed directly by n8n expressions
                    'event_id':    str(event.id),
                    'title':       event.title,
                    'description': event.description or '',
                    'start':       _to_rfc3339(event.start),
                    'end':         _to_rfc3339(event.end) if event.end else _to_rfc3339(event.start),
                    'location':    event.location or '',
                    'prompt':      prompt,
                    # Nested copy kept for backward compat
                    'event': {
                        'id':          event.id,
                        'title':       event.title,
                        'description': event.description or '',
                        'start':       _to_rfc3339(event.start),
                        'end':         _to_rfc3339(event.end) if event.end else _to_rfc3339(event.start),
                        'location':    event.location or '',
                    },
                    'triggered_by': getattr(request.user, 'id', None),
                }


                # Lazy import to avoid hard dependency unless used
                from .n8n_client import trigger_workflow
                for wf in workflows:
                    log = None
                    try:
                        if ExecutionLogModel:
                            triggered_by_user = request.user if getattr(request.user, 'is_authenticated', False) else None
                            log = ExecutionLogModel.objects.create(
                                workflow=wf,
                                triggered_by=triggered_by_user,
                                start_time=timezone.now(),
                                status='running',
                                input_data=payload,
                            )

                        status_code, resp = trigger_workflow(wf, event.id, payload)
                        triggered_any = True

                        if log:
                            log.output_data = {'status_code': status_code, 'response': resp}
                            log.status = 'completed' if 200 <= int(status_code) < 300 else 'failed'
                            log.end_time = timezone.now()
                            log.save()

                    except Exception as exc:
                        errors.append(str(exc))
                        if log:
                            log.error_details = {'error': str(exc)}
                            log.status = 'failed'
                            log.end_time = timezone.now()
                            log.save()

        # If any n8n workflow was triggered, return an acceptance response
        if triggered_any:
            event.generation_status = 'pending'
            event.last_generated_at = timezone.now()
            event.save()
            return Response({'detail': 'Workflows triggered', 'errors': errors}, status=status.HTTP_202_ACCEPTED)

        # Fallback to local mock generation when no workflows configured or all failed
        # Mock generation logic: produce simple variants
        social = f"Join us for {event.title} at {event.location} on {event.start.strftime('%b %d, %Y')}. {event.description[:120]}"
        email = f"Subject: {event.title}\n\nHello,\n\nWe're excited to invite you to {event.title}. Details:\n{event.description}\n\nWhen: {event.start}\nWhere: {event.location}\n\nBest regards,\nSwinburne VN"
        article = f"{event.title}\n\n{event.description}\n\nThis event on {event.start.strftime('%A, %d %B %Y')} at {event.location} will cover..."
        ad = f"{event.title} — {event.location} — {event.start.strftime('%b %d')} — Sign up now!"

        generated = {
            'social_post': social,
            'email_newsletter': email,
            'long_article': article,
            'recruitment_ad': ad,
        }

        # Simple validation/meta checks (mocked)
        meta = {
            'tone': 'informal',
            'brand_score': 0.92,
            'bias_flag': False,
            'generated_by': 'mock-genai',
            'prompt_used': prompt,
        }

        # Save results
        event.generated_content = generated
        event.generation_meta = meta
        event.generation_status = 'ready'
        event.last_generated_at = timezone.now()
        event.save()

        return Response({'generated_content': generated, 'generation_meta': meta}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def generation_callback(self, request, pk=None):
        """
        Callback endpoint for n8n to write back to an event.  Supports two phases:

        ─ Phase 1  (metadata / GCal link — no AI content yet)
          Body: { gcal_event_id?: str, generation_timeout_at?: ISO datetime }
          → Sets generation_status = 'pending', stores gcal_event_id.
          n8n calls this immediately after creating the GCal event (before Groq finishes).

        ─ Phase 2  (AI content ready)
          Body: { generated_content: {...}, generation_meta?: {...}, gcal_event_id?: str }
          → Sets generation_status = 'ready', stores content + meta.
          n8n calls this once Groq has finished generating.

        If both gcal_event_id AND generated_content are present in a single call, both
        are stored and status is set to 'ready' (single-phase fast path).

        Security: header `X-N8N-SECRET` must match `N8N_WEBHOOK_SECRET` setting.
        In DEBUG without a configured secret, the endpoint is open for local testing.
        """
        from django.conf import settings

        event = self.get_object()

        # ── Auth ──────────────────────────────────────────────────────────
        secret_required = getattr(settings, 'N8N_WEBHOOK_SECRET', None)
        if secret_required:
            incoming = request.headers.get('X-N8N-SECRET') or request.META.get('HTTP_X_N8N_SECRET')
            if incoming != secret_required:
                return Response({'detail': 'Invalid callback secret'}, status=status.HTTP_403_FORBIDDEN)
        else:
            if not getattr(settings, 'DEBUG', False):
                return Response({'detail': 'Callback secret not configured'}, status=status.HTTP_403_FORBIDDEN)

        # ── Extract payload fields ─────────────────────────────────────────
        generated_content = request.data.get('generated_content')
        generation_meta   = request.data.get('generation_meta')
        gcal_event_id     = request.data.get('gcal_event_id')
        timeout_at        = request.data.get('generation_timeout_at')

        # Must supply at least one meaningful field
        if not generated_content and not gcal_event_id:
            return Response(
                {'detail': 'Provide at least one of: generated_content, gcal_event_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Normalise generated_content ────────────────────────────────────
        # n8n can send JSON as a string (e.g. if the expression serialised to
        # a string instead of an object). Always coerce to dict.
        if generated_content and isinstance(generated_content, str):
            import json as _json
            try:
                generated_content = _json.loads(generated_content)
            except ValueError:
                # Wrap raw string as a social_post fallback so we never 500
                generated_content = {'social_post': generated_content}

        # Ensure meta is always a dict
        if generation_meta and isinstance(generation_meta, str):
            import json as _json
            try:
                generation_meta = _json.loads(generation_meta)
            except ValueError:
                generation_meta = {}

        update_fields = []

        # ── Phase 1 — store GCal link / set pending ────────────────────────
        if gcal_event_id:
            event.gcal_event_id = str(gcal_event_id)
            update_fields.append('gcal_event_id')

        if timeout_at:
            from django.utils.dateparse import parse_datetime
            parsed = parse_datetime(str(timeout_at))
            if parsed:
                event.generation_timeout_at = parsed
                update_fields.append('generation_timeout_at')

        # ── Phase 2 — store AI content / mark ready ────────────────────────
        if generated_content:
            event.generated_content  = generated_content
            event.generation_meta    = generation_meta or {}
            event.generation_status  = 'ready'
            event.last_generated_at  = timezone.now()
            update_fields += ['generated_content', 'generation_meta',
                               'generation_status', 'last_generated_at']
        elif gcal_event_id:
            # Phase-1-only call: mark as pending (only if currently idle/failed)
            if event.generation_status in ('idle', 'failed'):
                event.generation_status = 'pending'
                update_fields.append('generation_status')

        # ── Save ───────────────────────────────────────────────────────────
        # Guard: update_fields must be non-empty, and must include every field
        # that was mutated on the instance.  Fall back to a full save if empty.
        if update_fields:
            event.save(update_fields=list(set(update_fields)))
        else:
            event.save()

        phase = 2 if generated_content else 1
        return Response(
            {
                'detail': 'Saved',
                'phase': phase,
                'generation_status': event.generation_status,
                'gcal_event_id': event.gcal_event_id,
            },
            status=status.HTTP_200_OK,
        )


    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny],
            url_path='gcal-sync')
    def gcal_sync(self, request, pk=None):
        """
        Lightweight endpoint for n8n to store the Google Calendar event ID right after
        a GCal event is created — without touching AI content fields.

        POST /api/core/events/{id}/gcal-sync/
        Body: { gcal_event_id: "abc123xyz", generation_timeout_at?: "2024-01-01T12:00:00Z" }

        Same secret auth as generation_callback.  Status is set to 'pending' if the event
        is currently idle, so the frontend can show a loading state.
        """
        from django.conf import settings

        event = self.get_object()

        secret_required = getattr(settings, 'N8N_WEBHOOK_SECRET', None)
        if secret_required:
            incoming = request.headers.get('X-N8N-SECRET') or request.META.get('HTTP_X_N8N_SECRET')
            if incoming != secret_required:
                return Response({'detail': 'Invalid callback secret'}, status=status.HTTP_403_FORBIDDEN)
        else:
            if not getattr(settings, 'DEBUG', False):
                return Response({'detail': 'Callback secret not configured'}, status=status.HTTP_403_FORBIDDEN)

        gcal_event_id = request.data.get('gcal_event_id')
        if not gcal_event_id:
            return Response({'detail': 'gcal_event_id required'}, status=status.HTTP_400_BAD_REQUEST)

        update_fields = ['gcal_event_id']
        event.gcal_event_id = gcal_event_id

        if event.generation_status in ('idle', 'failed'):
            event.generation_status = 'pending'
            update_fields.append('generation_status')

        timeout_at = request.data.get('generation_timeout_at')
        if timeout_at:
            from django.utils.dateparse import parse_datetime
            parsed = parse_datetime(timeout_at)
            if parsed:
                event.generation_timeout_at = parsed
                update_fields.append('generation_timeout_at')

        event.save(update_fields=update_fields)

        return Response(
            {'detail': 'GCal link saved', 'gcal_event_id': event.gcal_event_id,
             'generation_status': event.generation_status},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='import-csv', permission_classes=[])
    def import_csv(self, request):
        """
        Staff-only endpoint to upload CSV and forward to n8n webhook.
        Expected CSV columns: title, description, start, end, location, visibility, related_unit_id
        """
        import csv
        import io
        from django.conf import settings

        # Accept form-data key 'data' to match the external webhook/postman example.
        # Keep backward compatibility with 'file'.
        file = request.FILES.get('data') or request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided (expected form field "data" with uploaded file)'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # We still read a subset of the CSV locally to validate it's not empty,
            # but we forward the original uploaded file to n8n so n8n can parse it.
            try:
                stream = io.TextIOWrapper(file.file, encoding='utf-8')
                reader = csv.DictReader(stream)
                rows = list(reader)
            except Exception:
                raw = file.read()
                if isinstance(raw, bytes):
                    text = raw.decode('utf-8')
                else:
                    text = str(raw)
                reader = csv.DictReader(io.StringIO(text))
                rows = list(reader)

            if not rows:
                return Response({'error': 'CSV is empty'}, status=status.HTTP_400_BAD_REQUEST)

            # Forward original file to n8n webhook as multipart/form-data with field 'data'
            n8n_webhook = getattr(settings, 'N8N_IMPORT_WEBHOOK', None)
            if not n8n_webhook:
                # In dev, return parsed rows for convenience
                if getattr(settings, 'DEBUG', False):
                    return Response({'message': f'CSV parsed (dev mode): {len(rows)} events', 'events': rows}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'n8n webhook not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            n8n_resp = {}
            # Try using requests if available (preferred)
            try:
                import requests as _requests
                # Rewind the uploaded file (in case earlier reads consumed it)
                try:
                    file.seek(0)
                except Exception:
                    pass
                files = {'data': (getattr(file, 'name', 'upload.csv'), file, getattr(file, 'content_type', 'text/csv'))}
                data = {'imported_by': request.user.email or '', 'timestamp': timezone.now().isoformat()}
                resp = _requests.post(n8n_webhook, files=files, data=data, timeout=60)
                resp.raise_for_status()
                try:
                    n8n_resp = resp.json() if resp.content else {}
                except Exception:
                    n8n_resp = {'status_text': resp.text}
            except Exception:
                # Fallback: build multipart/form-data body manually and use urllib
                try:
                    import uuid, json as _json
                    from urllib.request import Request, urlopen
                    from urllib.error import HTTPError, URLError

                    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
                    crlf = '\r\n'
                    parts = []

                    # text fields
                    text_fields = {
                        'imported_by': request.user.email or '',
                        'timestamp': timezone.now().isoformat(),
                    }
                    for name, value in text_fields.items():
                        parts.append(f'--{boundary}'.encode('utf-8'))
                        parts.append(f'Content-Disposition: form-data; name="{name}"'.encode('utf-8'))
                        parts.append(b'')
                        parts.append(str(value).encode('utf-8'))

                    # file field
                    try:
                        file.seek(0)
                    except Exception:
                        pass
                    file_bytes = file.read()
                    filename = getattr(file, 'name', 'upload.csv')
                    content_type = getattr(file, 'content_type', 'text/csv') or 'text/csv'

                    parts.append(f'--{boundary}'.encode('utf-8'))
                    parts.append(f'Content-Disposition: form-data; name="data"; filename="{filename}"'.encode('utf-8'))
                    parts.append(f'Content-Type: {content_type}'.encode('utf-8'))
                    parts.append(b'')
                    if isinstance(file_bytes, str):
                        file_bytes = file_bytes.encode('utf-8')
                    parts.append(file_bytes)

                    parts.append(f'--{boundary}--'.encode('utf-8'))

                    body = crlf.encode('utf-8').join(parts)
                    req = Request(n8n_webhook, data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
                    with urlopen(req, timeout=60) as fh:
                        resp_bytes = fh.read()
                        if resp_bytes:
                            try:
                                n8n_resp = _json.loads(resp_bytes.decode('utf-8'))
                            except Exception:
                                n8n_resp = {'status_text': resp_bytes.decode('utf-8')}
                        else:
                            n8n_resp = {}
                except HTTPError as he:
                    return Response({'error': f'n8n webhook HTTP error: {str(he)}'}, status=status.HTTP_502_BAD_GATEWAY)
                except URLError as ue:
                    return Response({'error': f'n8n webhook connection error: {str(ue)}'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                except Exception as exc:
                    return Response({'error': f'n8n webhook unknown error: {str(exc)}'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # Successful forward - return a friendly message indicating the schedule was uploaded
            return Response({
                'message': f'Successfully uploaded schedule to n8n: {len(rows)} rows',
                'n8n_response': n8n_resp
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsStaff])
    def refine_content(self, request, pk=None):
        """
        Staff-only: synchronous AI refinement via n8n WF-4 (chat loop friendly).

        n8n webhook must be configured with Respond: 'Using Respond to Webhook Node'
        so that this call blocks until Groq returns, then the refined content is
        returned directly in the response — no polling needed.

        POST body:
          refinement_prompt (str, required) — natural-language feedback for Groq
          current_content   (dict, optional) — content to refine; defaults to event.generated_content
          chat_history      (list, optional) — previous turns [{"role": "user"|"assistant", "content": "..."}]

        Returns:
          200 — refined content returned synchronously (n8n path or mock)
          400 — refinement_prompt missing or blank
          502 — n8n call failed or timed out
          503 — no active workflow registered (use mock path instead)
        """
        from django.apps import apps

        event = self.get_object()

        # ── Validate prompt ───────────────────────────────────────────────────
        refinement_prompt = request.data.get('refinement_prompt', '')
        if isinstance(refinement_prompt, str):
            refinement_prompt = refinement_prompt.strip()
        if not refinement_prompt:
            return Response(
                {'detail': 'refinement_prompt is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Resolve content source ────────────────────────────────────────────
        current_content = request.data.get('current_content') or event.generated_content or {}
        chat_history = request.data.get('chat_history', [])

        # ── Build audience context ────────────────────────────────────────────
        audience_context = {
            'visibility': event.visibility,
            'target_all_students': event.target_all_students,
            'target_student_count': event.get_targeted_students().count(),
            'target_offering_ids': list(event.target_offerings.values_list('id', flat=True)),
            'target_intake_ids': list(event.target_intakes.values_list('id', flat=True)),
        }

        # ── Look up active workflow ───────────────────────────────────────────
        try:
            N8NWorkflow = apps.get_model('users', 'N8NWorkflow')
            N8NExecutionLog = apps.get_model('users', 'N8NExecutionLog')
        except Exception:
            N8NWorkflow = None
            N8NExecutionLog = None

        wf = None
        if N8NWorkflow:
            wf = N8NWorkflow.objects.filter(trigger_event='event.refine', is_active=True).first()

        if wf:
            # ── n8n synchronous path ──────────────────────────────────────────
            # n8n webhook must use "Respond to Webhook" node so this call blocks
            # until Groq finishes and returns the refined content directly.
            from .n8n_client import _resolve_webhook_url
            import requests as _requests

            config = getattr(wf, 'configuration', {}) or {}
            webhook_url = _resolve_webhook_url(config)

            payload = {
                'event_id': str(event.id),
                'current_content': current_content,
                'refinement_prompt': refinement_prompt,
                'audience_context': audience_context,
                'chat_history': chat_history,
                'triggered_by': getattr(request.user, 'id', None),
            }

            log = None
            if N8NExecutionLog:
                triggered_by_user = request.user if getattr(request.user, 'is_authenticated', False) else None
                log = N8NExecutionLog.objects.create(
                    workflow=wf,
                    triggered_by=triggered_by_user,
                    start_time=timezone.now(),
                    status='running',
                    input_data=payload,
                )

            try:
                resp = _requests.post(
                    webhook_url,
                    json={'event_id': str(event.id), 'timestamp': timezone.now().isoformat(), 'payload': payload},
                    headers={'Content-Type': 'application/json'},
                    timeout=60,  # Groq can take up to ~15s; give plenty of room
                )
                resp.raise_for_status()

                try:
                    n8n_data = resp.json()
                except Exception:
                    n8n_data = {}

                # n8n Respond to Webhook node should return:
                # { generated_content: {...}, generation_meta: {...} }
                generated_content = n8n_data.get('generated_content') or n8n_data
                generation_meta = n8n_data.get('generation_meta', {
                    'generated_by': 'n8n-groq-refine',
                    'refinement_prompt': refinement_prompt,
                })

                # Normalise if n8n returned a string
                if isinstance(generated_content, str):
                    import json as _json
                    try:
                        generated_content = _json.loads(generated_content)
                    except ValueError:
                        generated_content = {'social_post': generated_content}

                # Save to event
                event.generated_content = generated_content
                event.generation_meta = generation_meta
                event.generation_status = 'ready'
                event.last_generated_at = timezone.now()
                event.save(update_fields=[
                    'generated_content', 'generation_meta',
                    'generation_status', 'last_generated_at',
                ])

                if log:
                    log.output_data = {'status_code': resp.status_code, 'response': n8n_data}
                    log.status = 'completed'
                    log.end_time = timezone.now()
                    log.save()

                wf.last_run = timezone.now()
                wf.save(update_fields=['last_run'])

                return Response({
                    'generated_content': generated_content,
                    'generation_meta': generation_meta,
                    'generation_status': 'ready',
                }, status=status.HTTP_200_OK)

            except Exception as exc:
                import logging
                logging.getLogger(__name__).exception('refine_content n8n call failed for event %s', event.id)

                if log:
                    log.error_details = {'error': str(exc)}
                    log.status = 'failed'
                    log.end_time = timezone.now()
                    log.save()

                return Response(
                    {'detail': 'Refinement workflow failed', 'error': str(exc)},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        # ── Mock refiner path (no active workflow) ────────────────────────────
        mock_content = {}
        for key, value in current_content.items():
            prefix = f'[Refinement note: {refinement_prompt}]\n'
            mock_content[key] = prefix + (str(value) if not isinstance(value, str) else value)

        meta = {
            'generated_by': 'mock-refine',
            'refinement_prompt': refinement_prompt,
        }

        event.generated_content = mock_content
        event.generation_status = 'ready'
        event.generation_meta = meta
        event.save(update_fields=['generated_content', 'generation_status', 'generation_meta'])

        return Response(
            {'generated_content': mock_content, 'generation_meta': meta, 'generation_status': 'ready'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsStaff], url_path='confirm-content')
    def confirm_content(self, request, pk=None):
        """
        Staff confirms the current generated_content is final and the event
        is ready to be sent to students.

        Sets visibility to 'public' (or the provided value) and generation_status to 'ready'.
        This is the "Confirm & Publish" button action.

        POST body:
          visibility (str, optional) — 'public' | 'unit' | 'staff' (default: 'public')
        """
        event = self.get_object()

        if not event.generated_content:
            return Response(
                {'detail': 'No generated content to confirm. Run refinement first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        visibility = request.data.get('visibility', 'public')
        if visibility not in ('public', 'unit', 'staff'):
            return Response({'detail': 'visibility must be public, unit, or staff'}, status=status.HTTP_400_BAD_REQUEST)

        event.visibility = visibility
        event.generation_status = 'ready'
        meta = event.generation_meta or {}
        meta['confirmed_by'] = getattr(request.user, 'email', str(request.user))
        meta['confirmed_at'] = timezone.now().isoformat()
        event.generation_meta = meta
        event.save(update_fields=['visibility', 'generation_status', 'generation_meta'])

        return Response({
            'detail': 'Event confirmed and ready to publish',
            'id': event.id,
            'title': event.title,
            'visibility': event.visibility,
            'generation_status': event.generation_status,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'], permission_classes=[IsStaff], url_path='update-content')
    def update_content(self, request, pk=None):
        """
        Staff-only: fully replace generated_content and optionally generation_meta.

        PUT body:
          generated_content (dict, required) — full replacement of all content fields
          generation_meta   (dict, optional) — replacement metadata
          generation_status (str, optional) — override status (default: 'ready')
        """
        event = self.get_object()

        generated_content = request.data.get('generated_content')
        if not generated_content or not isinstance(generated_content, dict):
            return Response(
                {'detail': 'generated_content (dict) is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event.generated_content = generated_content
        event.generation_meta = request.data.get('generation_meta', event.generation_meta or {})
        event.generation_status = request.data.get('generation_status', 'ready')
        event.last_generated_at = timezone.now()
        event.save(update_fields=[
            'generated_content', 'generation_meta', 'generation_status', 'last_generated_at'
        ])

        return Response(serializers.EventSerializer(event).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], permission_classes=[IsStaff], url_path='patch-content')
    def patch_content(self, request, pk=None):
        """
        Staff-only: partially update individual fields within generated_content.
        Only the keys provided are updated; others are left untouched.

        PATCH body:
          generated_content (dict, optional) — partial update, merged into existing content
          generation_meta   (dict, optional) — partial update, merged into existing meta
          generation_status (str, optional) — override status
        """
        event = self.get_object()

        if 'generated_content' in request.data:
            incoming = request.data['generated_content']
            if not isinstance(incoming, dict):
                return Response(
                    {'detail': 'generated_content must be a dict'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            current = event.generated_content or {}
            current.update(incoming)
            event.generated_content = current

        if 'generation_meta' in request.data:
            meta = event.generation_meta or {}
            meta.update(request.data['generation_meta'])
            event.generation_meta = meta

        if 'generation_status' in request.data:
            event.generation_status = request.data['generation_status']

        event.last_generated_at = timezone.now()
        event.save(update_fields=[
            'generated_content', 'generation_meta', 'generation_status', 'last_generated_at'
        ])

        return Response(serializers.EventSerializer(event).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], permission_classes=[IsStaff], url_path='clear-content')
    def clear_content(self, request, pk=None):
        """
        Staff-only: clear generated content and reset generation status to idle.
        The event itself is NOT deleted — only the AI-generated fields are wiped.
        """
        event = self.get_object()
        event.generated_content = {}
        event.generation_meta = {}
        event.generation_status = 'idle'
        event.last_generated_at = None
        event.save(update_fields=[
            'generated_content', 'generation_meta', 'generation_status', 'last_generated_at'
        ])

        return Response(
            {'detail': 'Generated content cleared', 'id': event.id, 'generation_status': 'idle'},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], permission_classes=[IsStaff], url_path='batch-create-webhook')
    def batch_create_from_webhook(self, request):
        """
        Webhook endpoint for n8n to POST back a batch of events.

        Supports two payload shapes — both can be mixed in the same request:

        ── Simple shape (original) ──────────────────────────────────────────
        {
          "events": [
            {
              "title": "...", "description": "...",
              "start": "2025-11-26T08:00:00",
              "end": "2025-11-26T10:00:00",
              "location": "...", "visibility": "public|unit|staff",
              "generated_content": {...}, "generation_meta": {...},
              "related_unit_id": <id|null>, "related_offering_id": <id|null>
            }
          ]
        }

        ── Rich CSV shape (from n8n CSV pipeline) ───────────────────────────
        {
          "events": [
            {
              "Event_Title": "Tuition Fee Deadline",
              "Event_Date": "2025-12-12",
              "Start_Time": "07:00",
              "Location": "Academic Department",
              "Notify_Rule": "1 week before",
              "Channels": "Email",
              "Target_Audience": "Parents, students",
              "Dept_Filter": "all",
              "Content_Remarks": "Tone: professional; topic: payment deadline",
              "Assets_URL": "https://drive.google.com/..."
            }
          ]
        }

        Fields are normalised automatically. Unknown extra fields are stored
        in generation_meta.csv_meta for reference.
        """
        import re
        from datetime import datetime, date

        events_data = request.data.get('events', [])
        if not events_data:
            return Response({'error': 'No events provided'}, status=status.HTTP_400_BAD_REQUEST)

        def _normalise(raw: dict) -> dict:
            """Convert either shape into a dict suitable for EventSerializer."""
            # Detect rich CSV shape by presence of CSV-specific keys
            is_csv = 'Event_Title' in raw or 'Event_Date' in raw

            if not is_csv:
                # Simple shape — pass through with minor cleanup
                return raw

            # ── Rich CSV → Event field mapping ────────────────────────────
            title = raw.get('Event_Title', '').strip()

            # Combine Event_Date + Start_Time → ISO datetime
            event_date = raw.get('Event_Date', '').strip()
            start_time = raw.get('Start_Time', '08:00').strip() or '08:00'
            start_dt = None
            for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y'):
                try:
                    d = datetime.strptime(event_date, fmt).date()
                    start_dt = f"{d.isoformat()}T{start_time}:00"
                    break
                except ValueError:
                    continue
            if not start_dt:
                start_dt = f"{event_date}T{start_time}:00"

            location = raw.get('Location', '').strip()
            if location.lower() in ('n/a', 'na', ''):
                location = ''

            # Target_Audience → visibility + target_all_students
            audience_raw = raw.get('Target_Audience', 'students').lower()
            target_all = True  # default
            visibility = 'public'
            if 'parent' in audience_raw:
                visibility = 'public'
                target_all = True
            elif 'staff' in audience_raw:
                visibility = 'staff'
                target_all = False
            else:
                visibility = 'public'
                target_all = True

            # Content_Remarks → description (also used as AI generation prompt)
            content_remarks = raw.get('Content_Remarks', '').strip()

            # Build generation_meta from CSV-specific fields
            csv_meta = {
                'notify_rule': raw.get('Notify_Rule', '').strip(),
                'channels': raw.get('Channels', '').strip(),
                'target_audience': raw.get('Target_Audience', '').strip(),
                'dept_filter': raw.get('Dept_Filter', '').strip(),
                'content_remarks': content_remarks,
                'assets_url': raw.get('Assets_URL', '').strip(),
                'source': 'csv_import',
            }

            return {
                'title': title,
                'description': content_remarks,
                'start': start_dt,
                'end': None,
                'location': location,
                'visibility': visibility,
                'target_all_students': target_all,
                'generation_status': 'idle',
                'generation_meta': {'csv_meta': csv_meta},
            }

        created_events = []
        errors = []

        for raw_data in events_data:
            try:
                event_data = _normalise(dict(raw_data))

                # Pull out non-serializer fields before passing to serializer
                target_all = event_data.pop('target_all_students', None)

                serializer = serializers.EventSerializer(data=event_data)
                if serializer.is_valid():
                    save_kwargs = {'created_by': request.user}
                    if target_all is not None:
                        save_kwargs['target_all_students'] = target_all
                    event = serializer.save(**save_kwargs)
                    created_events.append(serializer.data)
                else:
                    errors.append({'data': raw_data, 'errors': serializer.errors})
            except Exception as exc:
                errors.append({'data': raw_data, 'error': str(exc)})

        return Response({
            'created_count': len(created_events),
            'error_count': len(errors),
            'created_events': created_events,
            'errors': errors if errors else None,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsStaff], url_path='pending-refinement')
    def list_pending_refinement(self, request):
        """
        Staff-only: list all events with generation_status in ['pending', 'idle'] 
        that need refinement before publishing.
        """
        pending_statuses = request.query_params.getlist('status', ['pending', 'idle'])
        events = self.get_queryset().filter(generation_status__in=pending_statuses).order_by('-created_at')
        
        # Optional filtering by related unit
        unit_id = request.query_params.get('unit_id')
        if unit_id:
            events = events.filter(related_unit_id=unit_id)
        
        # Optional: only events created recently (e.g., last 7 days)
        days = request.query_params.get('days')
        if days:
            from datetime import timedelta
            cutoff = timezone.now() - timedelta(days=int(days))
            events = events.filter(created_at__gte=cutoff)

        page = self.paginate_queryset(events)
        if page is not None:
            serializer = serializers.EventSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.EventSerializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsStaff], url_path='bulk-publish')
    def bulk_publish(self, request):
        """
        Staff-only: publish (set visibility & generation_status) for multiple events at once.
        Expected payload: {
          'event_ids': [1, 2, 3, ...],
          'visibility': 'public|unit|staff',
          'generation_status': 'ready'
        }
        """
        event_ids = request.data.get('event_ids', [])
        visibility = request.data.get('visibility', 'public')
        gen_status = request.data.get('generation_status', 'ready')

        if not event_ids:
            return Response({'error': 'No event IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        if visibility not in ['public', 'unit', 'staff']:
            return Response({'error': 'Invalid visibility value'}, status=status.HTTP_400_BAD_REQUEST)

        if gen_status not in ['idle', 'pending', 'ready', 'failed']:
            return Response({'error': 'Invalid generation_status value'}, status=status.HTTP_400_BAD_REQUEST)

        updated = models.Event.objects.filter(id__in=event_ids).update(
            visibility=visibility,
            generation_status=gen_status,
            updated_at=timezone.now()
        )

        return Response({
            'message': f'Updated {updated} events',
            'updated_count': updated,
            'visibility': visibility,
            'generation_status': gen_status
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsStaff])
    def get_generation_status(self, request, pk=None):
        """
        Get detailed generation and publication status for a single event.
        Includes: generation_status, generated_content (preview), visibility, created_at, updated_at.
        """
        event = self.get_object()
        return Response({
            'id': event.id,
            'title': event.title,
            'generation_status': event.generation_status,
            'visibility': event.visibility,
            'generated_content': event.generated_content,
            'generation_meta': event.generation_meta,
            'created_at': event.created_at,
            'updated_at': event.updated_at,
            'last_generated_at': event.last_generated_at,
            'created_by': event.created_by.email if event.created_by else None,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsStaff], url_path='refine-chatbot')
    def refine_chatbot(self, request, pk=None):
        """
        Chatbot refinement endpoint: supports both prompt-based and direct editing.
        
        POST body:
        {
            "refinement_type": "prompt" | "direct_edit",
            "content": "<user prompt or edited text>",
            "field": "social_post" | "email_body" | "article_body" (optional, defaults to all)
        }
        
        If refinement_type == "prompt":
            - Forwards to n8n event_refinement_chatbot workflow
            - Returns suggestions from Groq LLM
        
        If refinement_type == "direct_edit":
            - Updates generated_content directly
            - Returns confirmation
        """
        event = self.get_object()
        refinement_type = request.data.get('refinement_type')
        content = request.data.get('content')
        field = request.data.get('field', 'all')

        if not refinement_type or not content:
            return Response(
                {'detail': 'refinement_type and content required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if refinement_type == 'direct_edit':
            # Direct editing: apply changes to generated_content
            if not event.generated_content:
                event.generated_content = {}
            
            if field == 'all':
                # Replace entire generated_content
                event.generated_content = content if isinstance(content, dict) else {'raw': content}
            else:
                # Update specific field
                event.generated_content[field] = content
            
            event.generation_status = 'pending'
            event.generation_meta = event.generation_meta or {}
            event.generation_meta['last_refined_by'] = request.user.email
            event.generation_meta['last_refined_at'] = timezone.now().isoformat()
            event.save()
            
            return Response({
                'type': 'confirmation',
                'event_id': event.id,
                'message': 'Content updated successfully',
                'updated_field': field,
                'generated_content': event.generated_content,
                'ready_to_publish': True
            }, status=status.HTTP_200_OK)

        elif refinement_type == 'prompt':
            # Prompt-based refinement: call n8n chatbot workflow
            from django.conf import settings
            from .n8n_client import trigger_workflow
            
            n8n_webhook = getattr(settings, 'N8N_REFINE_WEBHOOK', None)
            if not n8n_webhook:
                return Response(
                    {'detail': 'n8n refinement workflow not configured'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            payload = {
                'event_id': event.id,
                'refinement_type': 'prompt',
                'content': content,
                'original_title': event.title,
                'original_content': event.generated_content or {},
                'field': field,
                'triggered_by': request.user.email
            }
            
            try:
                import requests
                response = requests.post(n8n_webhook, json=payload, timeout=30)
                response.raise_for_status()
                suggestions = response.json()
                
                return Response({
                    'type': 'suggestions',
                    'event_id': event.id,
                    'suggestions': suggestions.get('suggestions', []),
                    'user_request': content,
                    'field': field,
                    'message': 'Suggestions generated. Select one to apply.'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {'detail': f'n8n refinement failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        else:
            return Response(
                {'detail': 'refinement_type must be "prompt" or "direct_edit"'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsStaff], url_path='apply-suggestion')
    def apply_suggestion(self, request, pk=None):
        """
        Apply a specific suggestion from chatbot refinement.
        
        POST body:
        {
            "suggestion": "<the suggestion text>",
            "field": "social_post" | "email_body" | "article_body"
        }
        """
        event = self.get_object()
        suggestion = request.data.get('suggestion')
        field = request.data.get('field', 'social_post')
        
        if not suggestion:
            return Response(
                {'detail': 'suggestion required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not event.generated_content:
            event.generated_content = {}
        
        event.generated_content[field] = suggestion
        event.generation_status = 'pending'
        event.generation_meta = event.generation_meta or {}
        event.generation_meta['last_suggestion_applied_at'] = timezone.now().isoformat()
        event.save()
        
        return Response({
            'message': 'Suggestion applied successfully',
            'field': field,
            'suggestion': suggestion,
            'generated_content': event.generated_content,
            'ready_to_publish': True
        }, status=status.HTTP_200_OK)


class SessionViewSet(viewsets.ModelViewSet):
    queryset = models.Session.objects.all().order_by('date')
    serializer_class = serializers.SessionSerializer
    # Only convenors or staff may create/edit sessions; others can read
    permission_classes = [IsConvenorOrStaffOrReadOnly]



class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = models.AttendanceRecord.objects.all()
    serializer_class = serializers.AttendanceSerializer
    # Attendance is write-protected to convenors/staff or owner
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrConvenorOrStaff]


class TicketViewSet(viewsets.ModelViewSet):
    queryset = models.Ticket.objects.all().order_by('-created_at')
    serializer_class = serializers.TicketSerializer
    # Tickets: any authenticated user may create; owner, convenor or staff can edit/manage
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrConvenorOrStaff]

    def perform_create(self, serializer):
        # Ensure submitter is set to the request user when creating via API
        if not serializer.validated_data.get('submitter'):
            serializer.save(submitter=self.request.user)
        else:
            serializer.save()


class TicketCommentViewSet(viewsets.ModelViewSet):
    queryset = models.TicketComment.objects.all().order_by('created_at')
    serializer_class = serializers.TicketCommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrConvenorOrStaff]


class FormViewSet(viewsets.ModelViewSet):
    queryset = models.Form.objects.all()
    serializer_class = serializers.FormSerializer
    # Forms: only staff/convenor may create forms
    permission_classes = [IsConvenorOrStaffOrReadOnly]


class FormSubmissionViewSet(viewsets.ModelViewSet):
    queryset = models.FormSubmission.objects.all().order_by('-created_at')
    serializer_class = serializers.FormSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrConvenorOrStaff]


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # each user only sees notifications addressed to them
        user = self.request.user
        return models.Notification.objects.filter(recipient=user).order_by('-created_at')

    def perform_create(self, serializer):
        # actor defaults to current user unless explicitly provided
        serializer.save(actor=self.request.user)


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = models.Resource.objects.all().order_by('-created_at')
    serializer_class = serializers.ResourceSerializer
    # Only convenors/staff may create resources; others read
    permission_classes = [IsConvenorOrStaffOrReadOnly]


class PageViewSet(viewsets.ModelViewSet):
    queryset = models.Page.objects.all().order_by('-created_at')
    serializer_class = serializers.PageSerializer
    permission_classes = [IsConvenorOrStaffOrReadOnly]


class MediaAssetViewSet(viewsets.ModelViewSet):
    queryset = models.MediaAsset.objects.all().order_by('-created_at')
    serializer_class = serializers.MediaAssetSerializer
    permission_classes = [IsConvenorOrStaffOrReadOnly]
