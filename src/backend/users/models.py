from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
import uuid

from src.backend.core.base_models import BaseModel


class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser
    """
    email = models.EmailField(unique=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    address_line1 = models.CharField(max_length=100, blank=True)
    address_line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, blank=True)
    user_type = models.CharField(max_length=20, choices=[
        ('student', 'Student'),
        ('staff', 'Staff'),
        ('unit_convenor', 'Unit Convenor'),
        ('auditor', 'Auditor'),
        ('parent', 'Parent'),
        ('admin', 'Administrator')
    ], default='student')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['email']

    def __str__(self):
        return f"{self.email} ({self.user_type})"


class Role(BaseModel):
    """
    Role model for defining custom roles with specific permissions
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict)

    def __str__(self):
        return self.name


class UserRole(BaseModel):
    """
    Intermediate model for user-role assignments with validity period
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.email} - {self.role.name}"


class Course(BaseModel):
    """
    Course model representing a full program of study
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_years = models.DecimalField(max_digits=3, decimal_places=1, default=3.0)
    credit_points = models.IntegerField(default=0)
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Unit(BaseModel):
    """
    Unit model representing individual subjects/units within courses
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credit_points = models.IntegerField(default=0)
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    convenor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='convened_units')
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class StudentProfile(BaseModel):
    """
    Additional student-specific information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    enrollment_date = models.DateField()
    expected_graduation = models.DateField(null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, null=True, blank=True)
    current_gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    academic_status = models.CharField(max_length=20, choices=[
        ('good', 'Good Standing'),
        ('probation', 'Academic Probation'),
        ('suspended', 'Suspended'),
        ('graduated', 'Graduated')
    ], default='good')

    def __str__(self):
        return f"{self.student_id} - {self.user.email}"

    def save(self, *args, **kwargs):
        # Ensure a student_id is set if missing
        if not self.student_id:
            import uuid
            self.student_id = f"S-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class ParentGuardian(BaseModel):
    """
    Parent/Guardian information linked to students
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    students = models.ManyToManyField(User, related_name='guardians')
    relationship = models.CharField(max_length=50, blank=True)
    is_emergency_contact = models.BooleanField(default=False)
    is_financial_responsible = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.relationship}"


class Enrollment(BaseModel):
    """
    Unit enrollment records for students
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20)
    year = models.IntegerField()
    status = models.CharField(max_length=20, choices=[
        ('enrolled', 'Enrolled'),
        ('withdrawn', 'Withdrawn'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='enrolled')
    grade = models.CharField(max_length=2, blank=True)
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'unit', 'semester', 'year')

    def __str__(self):
        return f"{self.student.email} - {self.unit.code} ({self.semester} {self.year})"


class Scholarship(BaseModel):
    """
    Scholarship information and awards
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    duration_semesters = models.IntegerField(default=1)
    requirements = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ScholarshipApplication(BaseModel):
    """
    Student applications for scholarships
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE)
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('waitlisted', 'Waitlisted')
    ], default='pending')
    documents = models.JSONField(default=list)
    reviewer_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.email} - {self.scholarship.name}"


class AuditLog(BaseModel):
    """
    Audit log for tracking important system actions
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)

    def __str__(self):
        return f"{self.created_at} - {self.user.email if self.user else 'System'} - {self.action}"


class N8NWorkflow(BaseModel):
    """
    N8N workflow configurations and triggers
    """
    workflow_id = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger_event = models.CharField(max_length=50)
    configuration = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    error_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.workflow_id})"


class N8NExecutionLog(BaseModel):
    """
    Execution logs for N8N workflows
    """
    workflow = models.ForeignKey(N8NWorkflow, on_delete=models.CASCADE)
    execution_id = models.UUIDField(default=uuid.uuid4, unique=True)
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(null=True, blank=True)
    error_details = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.workflow.name} - {self.execution_id}"
