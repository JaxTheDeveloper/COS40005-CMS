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


class Transcript(models.Model):
    """
    Academic transcript tracking past enrollments and academic history
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transcripts')
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='transcript_entry')
    
    # Academic details
    unit_code = models.CharField(max_length=20)  # Denormalized for easier querying
    unit_name = models.CharField(max_length=200)  # Denormalized
    semester = models.CharField(max_length=2)  # S1, S2, S3, SS, WS
    year = models.IntegerField()
    credit_points = models.IntegerField(default=0)
    
    # Grade information
    grade = models.CharField(max_length=2, blank=True)  # HD, D, C, P, F, etc.
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)  # GPA contribution
    
    # Status
    status = models.CharField(max_length=20, choices=Enrollment.STATUS_CHOICES)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-year', 'semester', 'unit_code']
        indexes = [
            models.Index(fields=['student', '-year', 'semester']),
            models.Index(fields=['student', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.email} - {self.unit_code} ({self.semester} {self.year})"
    
    def calculate_grade_point(self):
        """Calculate grade point based on grade"""
        grade_points = {
            'HD': 4.0, 'D': 3.0, 'C': 2.0, 'P': 1.0, 'F': 0.0,
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'F': 0.0
        }
        return grade_points.get(self.grade.upper(), None)
    
    def save(self, *args, **kwargs):
        # Auto-populate from enrollment if not set
        if self.enrollment:
            if not self.unit_code:
                self.unit_code = self.enrollment.offering.unit.code
            if not self.unit_name:
                self.unit_name = self.enrollment.offering.unit.name
            if not self.semester:
                self.semester = self.enrollment.offering.semester
            if not self.year:
                self.year = self.enrollment.offering.year
            if not self.credit_points:
                self.credit_points = self.enrollment.offering.unit.credit_points
            if not self.grade:
                self.grade = self.enrollment.grade
            if not self.marks:
                self.marks = self.enrollment.marks
            if not self.status:
                self.status = self.enrollment.status
            if not self.completion_date:
                self.completion_date = self.enrollment.completion_date
            
            # Calculate grade point
            if self.grade and not self.grade_point:
                self.grade_point = self.calculate_grade_point()
        
        super().save(*args, **kwargs)