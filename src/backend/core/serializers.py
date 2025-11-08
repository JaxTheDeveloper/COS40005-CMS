from rest_framework import serializers
from . import models


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Session
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AttendanceRecord
        fields = '__all__'


class TicketSerializer(serializers.ModelSerializer):
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
