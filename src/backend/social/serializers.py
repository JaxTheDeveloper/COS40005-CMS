from rest_framework import serializers
from .models import SocialGold, SocialGoldTransaction
from src.backend.users.serializers import UserSerializer


class SocialGoldSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    
    class Meta:
        model = SocialGold
        fields = ['id', 'student', 'current_balance', 'lifetime_earned', 'last_updated']


class SocialGoldTransactionSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    awarded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = SocialGoldTransaction
        fields = ['id', 'student', 'amount', 'transaction_type', 'reason',
                 'details', 'awarded_by', 'created_at']
        read_only_fields = ['created_at']


class AwardGoldSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=200)
    details = serializers.CharField(required=False, allow_blank=True)