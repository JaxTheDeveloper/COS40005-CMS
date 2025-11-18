from rest_framework import serializers
from .models import Unit, SemesterOffering


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'code', 'name', 'description', 'credit_points', 'department', 'convenor']


class SemesterOfferingSerializer(serializers.ModelSerializer):
    unit = UnitSerializer(read_only=True)
    # include notes so frontend can read scheduling metadata persisted by the seeder
    class Meta:
        model = SemesterOffering
        fields = ['id', 'unit', 'year', 'semester', 'enrollment_start', 'enrollment_end', 'capacity', 'current_enrollment', 'is_active', 'notes']
