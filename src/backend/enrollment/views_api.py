from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Enrollment
from .serializers import EnrollmentSerializer, EnrollmentCreateSerializer


class EnrollmentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Enrollment.objects.all()
        return Enrollment.objects.filter(student=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EnrollmentCreateSerializer
        return EnrollmentSerializer

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        enrollment = self.get_object()
        if enrollment.student != request.user and not request.user.is_staff:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            
        enrollment.status = 'WITHDRAWN'
        enrollment.save()
        return Response({'status': 'withdrawn'})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if not request.user.is_staff:
            return Response({'error': 'Staff only'}, status=status.HTTP_403_FORBIDDEN)
            
        enrollment = self.get_object()
        enrollment.status = 'ENROLLED'
        enrollment.save()
        return Response({'status': 'approved'})