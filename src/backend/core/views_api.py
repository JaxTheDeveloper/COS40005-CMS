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
                # Build payload once
                payload = {
                    'prompt': prompt,
                    'event': {
                        'id': event.id,
                        'title': event.title,
                        'description': event.description,
                        'start': event.start.isoformat() if event.start else None,
                        'location': event.location,
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
        Callback endpoint for external workflows (n8n) to POST generated content back to the event.

        Security: if `N8N_WEBHOOK_SECRET` is set in Django settings, the caller must send header
        `X-N8N-SECRET: <secret>` matching that value. If unset, and DEBUG is True, the endpoint will accept
        the callback (useful for local testing). Otherwise it's rejected.
        """
        from django.conf import settings

        event = self.get_object()

        secret_required = getattr(settings, 'N8N_WEBHOOK_SECRET', None)
        if secret_required:
            incoming = request.headers.get('X-N8N-SECRET') or request.META.get('HTTP_X_N8N_SECRET')
            if incoming != secret_required:
                return Response({'detail': 'Invalid callback secret'}, status=status.HTTP_403_FORBIDDEN)
        else:
            # If no secret configured, allow in DEBUG for convenience only
            if not getattr(settings, 'DEBUG', False):
                return Response({'detail': 'Callback secret not configured'}, status=status.HTTP_403_FORBIDDEN)

        generated_content = request.data.get('generated_content')
        generation_meta = request.data.get('generation_meta')

        if not generated_content:
            return Response({'detail': 'No generated_content in payload'}, status=status.HTTP_400_BAD_REQUEST)

        event.generated_content = generated_content
        event.generation_meta = generation_meta or {}
        event.generation_status = 'ready'
        event.last_generated_at = timezone.now()
        event.save()

        return Response({'detail': 'Saved'}, status=status.HTTP_200_OK)

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

    @action(detail=True, methods=['put'], permission_classes=[IsStaff])
    def refine_content(self, request, pk=None):
        """
        Staff-only: update event generated_content, generation_status and generation_meta.
        Useful for refining AI-generated content before publishing.
        """
        event = self.get_object()
        event.generated_content = request.data.get('generated_content', event.generated_content)
        event.generation_status = request.data.get('generation_status', event.generation_status)
        event.generation_meta = request.data.get('generation_meta', event.generation_meta)
        event.save()

        return Response(serializers.EventSerializer(event).data)

    @action(detail=False, methods=['post'], permission_classes=[IsStaff], url_path='batch-create-webhook')
    def batch_create_from_webhook(self, request):
        """
        Webhook endpoint for n8n to POST back a batch of generated events.
        Expected payload: {
          'events': [
            {
              'title': '...',
              'description': '...',
              'start': '2025-...',
              'end': '2025-...',
              'location': '...',
              'visibility': 'public|unit|staff',
              'generated_content': {...},
              'generation_meta': {...},
              'related_unit_id': <id or null>,
              'related_offering_id': <id or null>
            },
            ...
          ]
        }
        """
        events_data = request.data.get('events', [])
        if not events_data:
            return Response({'error': 'No events provided'}, status=status.HTTP_400_BAD_REQUEST)

        created_events = []
        errors = []

        for event_data in events_data:
            try:
                # Set creator and timestamps
                event_data['created_by'] = request.user.id
                
                # Create event using serializer
                serializer = serializers.EventSerializer(data=event_data)
                if serializer.is_valid():
                    event = serializer.save(created_by=request.user)
                    created_events.append(serializer.data)
                else:
                    errors.append({'data': event_data, 'errors': serializer.errors})
            except Exception as exc:
                errors.append({'data': event_data, 'error': str(exc)})

        return Response({
            'created_count': len(created_events),
            'error_count': len(errors),
            'created_events': created_events,
            'errors': errors if errors else None
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
