from rest_framework import serializers
from .models import Enrollment, Transcript
from src.backend.academic.serializers import SemesterOfferingSerializer
from src.backend.users.serializers import UserSerializer


class EnrollmentSerializer(serializers.ModelSerializer):
    offering = SemesterOfferingSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'offering', 'status', 'grade', 'marks',
                 'withdrawn_date', 'completion_date', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['offering']  # Only need offering ID when creating enrollment

    def create(self, validated_data):
        # Set student to current user
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)


class TranscriptSerializer(serializers.ModelSerializer):
    """Serializer for academic transcripts"""
    student = UserSerializer(read_only=True)
    
    class Meta:
        model = Transcript
        fields = ['id', 'student', 'enrollment', 'unit_code', 'unit_name', 
                 'semester', 'year', 'credit_points', 'grade', 'marks', 
                 'grade_point', 'status', 'completion_date', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']