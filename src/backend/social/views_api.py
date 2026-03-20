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

    @action(
        detail=False, methods=['post'],
        url_path='award',
        permission_classes=[permissions.IsAdminUser],
    )
    def n8n_award(self, request):
        """
        n8n-callable endpoint to award Social Gold to a student.

        POST /api/social/transactions/award/
        Body: { student_id, amount, transaction_type (AWARD|BONUS), reason, details? }

        Protected by IsAdminUser — n8n authenticates with a staff service-account JWT
        (see N8N_SERVICE_ACCOUNT_TOKEN in .env).
        """
        from django.contrib.auth import get_user_model
        from .models import SocialGold
        User = get_user_model()

        student_id = request.data.get('student_id')
        amount = request.data.get('amount')
        txn_type = request.data.get('transaction_type', 'AWARD')
        reason = request.data.get('reason', '')
        details = request.data.get('details', '')

        # --- Validate inputs ---
        if not student_id or not amount:
            return Response(
                {'error': 'student_id and amount are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if txn_type not in ('AWARD', 'BONUS'):
            return Response(
                {'error': 'transaction_type must be AWARD or BONUS'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'amount must be a positive integer'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            student = User.objects.get(pk=student_id, user_type='student')
        except User.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        # --- Atomic DB write ---
        with transaction.atomic():
            txn = SocialGoldTransaction.objects.create(
                student=student,
                amount=amount,
                transaction_type=txn_type,
                reason=reason,
                details=details,
                awarded_by=request.user,
            )
            balance, _ = SocialGold.objects.get_or_create(
                student=student,
                defaults={'current_balance': 0, 'lifetime_earned': 0},
            )
            balance.current_balance += amount
            balance.lifetime_earned += amount
            balance.save(update_fields=['current_balance', 'lifetime_earned'])

        return Response(
            {
                'transaction_id': txn.id,
                'student_id': student_id,
                'new_balance': balance.current_balance,
                'lifetime_earned': balance.lifetime_earned,
            },
            status=status.HTTP_201_CREATED,
        )