from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import SocialGold, SocialGoldTransaction
from .serializers import (
    SocialGoldSerializer, SocialGoldTransactionSerializer, AwardGoldSerializer
)


class SocialGoldViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SocialGoldSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SocialGold.objects.all()
        return SocialGold.objects.filter(student=user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def award(self, request, pk=None):
        social_gold = self.get_object()
        serializer = AwardGoldSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        
        with transaction.atomic():
            # Create transaction
            SocialGoldTransaction.objects.create(
                student=social_gold.student,
                amount=data['amount'],
                transaction_type='AWARD',
                reason=data['reason'],
                details=data.get('details', ''),
                awarded_by=request.user
            )
            
            # Update balance
            social_gold.current_balance += data['amount']
            social_gold.lifetime_earned += data['amount']
            social_gold.save()
            
        return Response({'status': 'awarded'})


class SocialGoldTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SocialGoldTransactionSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SocialGoldTransaction.objects.all()
        return SocialGoldTransaction.objects.filter(student=user)