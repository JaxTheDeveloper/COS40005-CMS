from rest_framework import serializers
from .models import Unit, SemesterOffering


class UnitSerializer(serializers.ModelSerializer):
    # is_elective is injected at runtime by the enrollment dashboard when a
    # student has a major assigned; None means "no major context / unknown".
    is_elective = serializers.SerializerMethodField()

    def get_is_elective(self, obj):
        return getattr(obj, '_is_elective', None)

    class Meta:
        model = Unit
        fields = ['id', 'code', 'name', 'description', 'credit_points', 'department', 'convenor', 'is_elective']


class SemesterOfferingSerializer(serializers.ModelSerializer):
    unit = UnitSerializer(read_only=True)
    # include notes so frontend can read scheduling metadata persisted by the seeder
    class Meta:
        model = SemesterOffering
        fields = ['id', 'unit', 'year', 'semester', 'enrollment_start', 'enrollment_end', 'capacity', 'current_enrollment', 'is_active', 'notes']
