from rest_framework import viewsets, filters, permissions, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

from .models import N8NWorkflow, N8NExecutionLog
from .serializers import (
    UserSerializer, N8NWorkflowSerializer, N8NExecutionLogSerializer
)

User = get_user_model()


class StudentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        students = User.objects.filter(user_type='student')
        serializer = UserSerializer(students, many=True)
        return Response(serializer.data)


class TokenObtainPairCompatView(APIView):
    """Compatibility endpoint: accepts 'username' or 'email' and returns JWT tokens.

    Our User model uses email as USERNAME_FIELD. This view allows clients that still
    send 'username' (legacy) to authenticate by mapping username -> email.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        # If client sent 'username' but not 'email', try to map it.
        if 'username' in data and 'email' not in data:
            username = data.get('username')
            try:
                user = User.objects.get(username=username)
                data['email'] = user.email
            except User.DoesNotExist:
                pass

        serializer = TokenObtainPairSerializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# N8N Workflow management API (staff-only)
# ---------------------------------------------------------------------------

class N8NWorkflowViewSet(viewsets.ModelViewSet):
    """
    Staff-only CRUD for registering and managing n8n webhook workflows.

    POST   /api/users/n8n-workflows/        — register a workflow
    GET    /api/users/n8n-workflows/        — list all (filterable by trigger_event, is_active)
    GET    /api/users/n8n-workflows/{id}/   — retrieve one
    PATCH  /api/users/n8n-workflows/{id}/   — update (e.g. enable/disable, change URL)
    DELETE /api/users/n8n-workflows/{id}/   — deregister

    Example body for POST:
      {
        "name": "Event Content Generator",
        "trigger_event": "event.generate",
        "is_active": true,
        "configuration": {
          "webhook_url": "http://cos40005_n8n:5678/webhook/event-generate"
        }
      }
    """
    queryset = N8NWorkflow.objects.all().order_by('-created_at')
    serializer_class = N8NWorkflowSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['trigger_event', 'name']

    def get_queryset(self):
        qs = super().get_queryset()
        trigger = self.request.query_params.get('trigger_event')
        active = self.request.query_params.get('is_active')
        if trigger:
            qs = qs.filter(trigger_event=trigger)
        if active is not None:
            qs = qs.filter(is_active=(active.lower() == 'true'))
        return qs


class N8NExecutionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Staff-only read access to n8n execution history.

    GET /api/users/n8n-logs/               — list all logs (filter by ?workflow=<id>)
    GET /api/users/n8n-logs/{id}/          — retrieve one execution log
    """
    queryset = N8NExecutionLog.objects.all().order_by('-start_time')
    serializer_class = N8NExecutionLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = super().get_queryset()
        wf_id = self.request.query_params.get('workflow')
        status_filter = self.request.query_params.get('status')
        if wf_id:
            qs = qs.filter(workflow_id=wf_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs
