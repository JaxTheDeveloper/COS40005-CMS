from rest_framework import viewsets, permissions
from .models import Unit, SemesterOffering
from .serializers import UnitSerializer, SemesterOfferingSerializer


class UnitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Unit.objects.filter(is_active=True)
    serializer_class = UnitSerializer
    permission_classes = [permissions.AllowAny]


class SemesterOfferingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SemesterOffering.objects.filter(is_active=True)
    serializer_class = SemesterOfferingSerializer
    permission_classes = [permissions.AllowAny]
