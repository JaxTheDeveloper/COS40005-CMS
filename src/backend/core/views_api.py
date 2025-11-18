from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

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
    queryset = models.FormSubmission.objects.all().order_by('-submitted_at')
    serializer_class = serializers.FormSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrConvenorOrStaff]


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = models.Notification.objects.all().order_by('-created_at')
    serializer_class = serializers.NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]


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
