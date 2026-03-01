from rest_framework import serializers
from django.contrib.auth import get_user_model
from . import models
from src.backend.academic.models import Intake, SemesterOffering

User = get_user_model()


class IntakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intake
        fields = ['id', 'semester', 'year']


class EventSerializer(serializers.ModelSerializer):
    # nested relations for clarity
    target_students = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    target_offerings = serializers.PrimaryKeyRelatedField(many=True, queryset=SemesterOffering.objects.all(), required=False)
    target_intakes = IntakeSerializer(many=True, required=False)

    class Meta:
        model = models.Event
        # explicitly list fields to ensure new ones included
        fields = [
            'id', 'title', 'description', 'start', 'end', 'location', 'visibility',
            'attendees',
            'target_all_students', 'target_students', 'target_offerings', 'target_intakes',
            'related_unit', 'related_offering',
            'generated_content', 'generation_status', 'generation_meta', 'last_generated_at',
            'created_at', 'updated_at', 'deleted_at', 'is_deleted',
        ]

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Session
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AttendanceRecord
        fields = '__all__'


class TicketSerializer(serializers.ModelSerializer):
    # Submitter should default to the requesting user when created through the API
    submitter = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = models.Ticket
        fields = '__all__'


class TicketCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TicketComment
        fields = '__all__'


class FormSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Form
        fields = '__all__'


class FormSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FormSubmission
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notification
        fields = '__all__'


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Resource
        fields = '__all__'


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Page
        fields = '__all__'


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MediaAsset
        fields = '__all__'
