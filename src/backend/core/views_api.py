from rest_framework import viewsets, permissions
from . import models, serializers
from .permissions import IsStaff, IsConvenor, IsOwnerOrReadOnly


class EventViewSet(viewsets.ModelViewSet):
    queryset = models.Event.objects.all().order_by('-start')
    serializer_class = serializers.EventSerializer
    # Events: authenticated users can list/read; convenors and staff can create/edit
    permission_classes = [permissions.IsAuthenticated]



class SessionViewSet(viewsets.ModelViewSet):
    queryset = models.Session.objects.all().order_by('date')
    serializer_class = serializers.SessionSerializer
    # Only convenors or staff may create/edit sessions; others can read
    permission_classes = [permissions.IsAuthenticated]



class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = models.AttendanceRecord.objects.all()
    serializer_class = serializers.AttendanceSerializer
    # Attendance is write-protected to convenors/staff or owner
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]


class TicketViewSet(viewsets.ModelViewSet):
    queryset = models.Ticket.objects.all().order_by('-created_at')
    serializer_class = serializers.TicketSerializer
    # Tickets: any authenticated user may create; staff can manage
    permission_classes = [permissions.IsAuthenticated]


class TicketCommentViewSet(viewsets.ModelViewSet):
    queryset = models.TicketComment.objects.all().order_by('created_at')
    serializer_class = serializers.TicketCommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]


class FormViewSet(viewsets.ModelViewSet):
    queryset = models.Form.objects.all()
    serializer_class = serializers.FormSerializer
    # Forms: only staff/convenor may create forms
    permission_classes = [permissions.IsAuthenticated]


class FormSubmissionViewSet(viewsets.ModelViewSet):
    queryset = models.FormSubmission.objects.all().order_by('-submitted_at')
    serializer_class = serializers.FormSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = models.Notification.objects.all().order_by('-created_at')
    serializer_class = serializers.NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = models.Resource.objects.all().order_by('-created_at')
    serializer_class = serializers.ResourceSerializer
    # Only convenors/staff may create resources; others read
    permission_classes = [permissions.IsAuthenticated]


class PageViewSet(viewsets.ModelViewSet):
    queryset = models.Page.objects.all().order_by('-created_at')
    serializer_class = serializers.PageSerializer
    permission_classes = [permissions.IsAuthenticated]


class MediaAssetViewSet(viewsets.ModelViewSet):
    queryset = models.MediaAsset.objects.all().order_by('-created_at')
    serializer_class = serializers.MediaAssetSerializer
    permission_classes = [permissions.IsAuthenticated]
