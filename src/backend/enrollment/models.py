from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from src.backend.users.models import User
from src.backend.academic.models import Unit, SemesterOffering


class Enrollment(models.Model):
    """
    Unit enrollment records for students with prerequisite validation
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('ENROLLED', 'Enrolled'),
        ('WITHDRAWN', 'Withdrawn'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    offering = models.ForeignKey(SemesterOffering, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    grade = models.CharField(max_length=2, blank=True)
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    withdrawn_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'offering')
        ordering = ['-offering__year', 'offering__semester', 'offering__unit__code']

    def __str__(self):
        return f"{self.student.email} - {self.offering}"

    def clean(self):
        if not self.pk:  # Only check on creation
            self._validate_prerequisites()
            self._validate_anti_requisites()
            self._validate_enrollment_period()
            self._validate_capacity()

    def _validate_prerequisites(self):
        """Check if student has completed all prerequisites"""
        prerequisites = self.offering.unit.prerequisites.all()
        if not prerequisites:
            return

        completed_units = set(
            Enrollment.objects.filter(
                student=self.student,
                status='COMPLETED',
                offering__unit__in=prerequisites
            ).values_list('offering__unit_id', flat=True)
        )
        
        missing = [p for p in prerequisites if p.id not in completed_units]
        if missing:
            raise ValidationError(
                f'Missing prerequisites: {", ".join(str(m) for m in missing)}'
            )

    def _validate_anti_requisites(self):
        """Check if student has completed or is enrolled in any anti-requisites"""
        anti_requisites = self.offering.unit.anti_requisites.all()
        if not anti_requisites:
            return

        conflicting = Enrollment.objects.filter(
            student=self.student,
            offering__unit__in=anti_requisites,
            status__in=['ENROLLED', 'COMPLETED']
        ).first()

        if conflicting:
            raise ValidationError(
                f'Cannot enroll: Already completed/enrolled in anti-requisite {conflicting.offering.unit}'
            )

    def _validate_enrollment_period(self):
        """Check if enrollment is within the allowed period"""
        now = timezone.now()
        if now < self.offering.enrollment_start:
            raise ValidationError('Enrollment period has not started yet.')
        if now > self.offering.enrollment_end:
            raise ValidationError('Enrollment period has ended.')

    def _validate_capacity(self):
        """Check if the offering has available capacity"""
        if self.offering.is_full():
            raise ValidationError('This offering has reached its maximum capacity.')

    def withdraw(self):
        """Withdraw from the enrollment"""
        if self.status not in ['PENDING', 'ENROLLED']:
            raise ValidationError('Can only withdraw from pending or active enrollments.')
        
        self.status = 'WITHDRAWN'
        self.withdrawn_date = timezone.now()
        self.save()

        # Update current enrollment count
        self.offering.current_enrollment = models.F('current_enrollment') - 1
        self.offering.save()


class EnrollmentApproval(models.Model):
    """
    Tracks approval process for enrollments that require it
    """
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='approval')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    approved_at = models.DateTimeField(null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Approval for {self.enrollment}"

    def approve(self, approver, notes=''):
        """Approve the enrollment"""
        if self.enrollment.status != 'PENDING':
            raise ValidationError('Can only approve pending enrollments.')
        
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.notes = notes
        self.save()

        # Update enrollment status
        self.enrollment.status = 'ENROLLED'
        self.enrollment.save()

        # Update current enrollment count
        self.enrollment.offering.current_enrollment = models.F('current_enrollment') + 1
        self.enrollment.offering.save()