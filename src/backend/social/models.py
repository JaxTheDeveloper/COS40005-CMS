from django.db import models
from django.core.validators import MinValueValidator
from src.backend.users.models import User


class SocialGold(models.Model):
    """
    Tracks social gold points earned by students
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_gold')
    current_balance = models.PositiveIntegerField(default=0)
    lifetime_earned = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Social Gold Balance'
        verbose_name_plural = 'Social Gold Balances'

    def __str__(self):
        return f"{self.student.email} - {self.current_balance} points"


class SocialGoldTransaction(models.Model):
    """
    Records individual social gold transactions
    """
    TRANSACTION_TYPES = [
        ('AWARD', 'Award Points'),
        ('DEDUCT', 'Deduct Points'),
        ('EXPIRE', 'Points Expiry'),
        ('BONUS', 'Bonus Points'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_gold_transactions')
    amount = models.IntegerField()  # Can be negative for deductions
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    reason = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='awarded_social_gold')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.email} - {self.amount} points - {self.reason}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount == 0:
            raise ValidationError('Transaction amount cannot be zero.')
        if self.transaction_type in ['AWARD', 'BONUS'] and self.amount < 0:
            raise ValidationError('Award and bonus transactions must have positive amounts.')
        if self.transaction_type in ['DEDUCT', 'EXPIRE'] and self.amount > 0:
            raise ValidationError('Deduct and expire transactions must have negative amounts.')


class Achievement(models.Model):
    """
    Defines achievements that can be earned through social gold
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.PositiveIntegerField()
    badge_image = models.ImageField(upload_to='achievement_badges/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['points_required', 'name']

    def __str__(self):
        return f"{self.name} ({self.points_required} points)"


class StudentAchievement(models.Model):
    """
    Records achievements earned by students
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    points_at_earning = models.PositiveIntegerField()  # Snapshot of points when earned

    class Meta:
        unique_together = ('student', 'achievement')
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.student.email} - {self.achievement.name}"