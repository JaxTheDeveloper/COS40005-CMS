from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import N8NWorkflow, N8NExecutionLog

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 
                 'is_staff', 'user_type', 'department', 'position', 'bio',
                 'profile_image', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new user
    """
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'confirm_password', 
                 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class N8NWorkflowSerializer(serializers.ModelSerializer):
    """Serializer for managing n8n webhook workflow registrations."""

    class Meta:
        model = N8NWorkflow
        fields = [
            'id', 'workflow_id', 'name', 'description', 'trigger_event',
            'configuration', 'is_active', 'last_run', 'error_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['workflow_id', 'last_run', 'error_count', 'created_at', 'updated_at']


class N8NExecutionLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for n8n execution history logs."""
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    triggered_by_email = serializers.SerializerMethodField()

    class Meta:
        model = N8NExecutionLog
        fields = [
            'id', 'execution_id', 'workflow', 'workflow_name',
            'triggered_by_email', 'start_time', 'end_time', 'status',
            'input_data', 'output_data', 'error_details',
        ]
        read_only_fields = fields

    def get_triggered_by_email(self, obj):
        return obj.triggered_by.email if obj.triggered_by else None