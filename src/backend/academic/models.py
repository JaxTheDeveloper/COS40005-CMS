from django.db import models
from django.core.exceptions import ValidationError
from src.backend.users.models import User
from src.backend.core.base_models import BaseModel


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

    class Meta:
        ordering = ['code']

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
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='required_for')
    anti_requisites = models.ManyToManyField('self', blank=True, symmetrical=True)
    convenor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='academic_units_convened')
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        # Ensure a unit isn't its own prerequisite or anti-requisite
        if self.pk:
            if self in self.prerequisites.all():
                raise ValidationError('A unit cannot be its own prerequisite.')
            if self in self.anti_requisites.all():
                raise ValidationError('A unit cannot be its own anti-requisite.')


class SemesterOffering(BaseModel):
    """
    Represents when a unit is offered in a specific semester
    """
    SEMESTER_CHOICES = [
        ('S1', 'Semester 1'),
        ('S2', 'Semester 2'),
        ('S3', 'Semester 3'),
        ('SS', 'Summer Session'),
        ('WS', 'Winter Session'),
    ]

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='offerings')
    year = models.IntegerField()
    semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES)
    enrollment_start = models.DateTimeField()
    enrollment_end = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=0)
    current_enrollment = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('unit', 'year', 'semester')
        ordering = ['-year', 'semester', 'unit__code']

    def __str__(self):
        return f"{self.unit.code} - {self.get_semester_display()} {self.year}"

    def clean(self):
        if self.enrollment_start and self.enrollment_end:
            if self.enrollment_start >= self.enrollment_end:
                raise ValidationError('Enrollment start must be before enrollment end.')

    def is_full(self):
        return self.current_enrollment >= self.capacity if self.capacity > 0 else False


class UnitResource(BaseModel):
    """
    Resources (files, links) associated with a unit
    """
    RESOURCE_TYPES = [
        ('OUTLINE', 'Unit Outline'),
        ('TEXTBOOK', 'Textbook'),
        ('READING', 'Required Reading'),
        ('LINK', 'External Link'),
        ('OTHER', 'Other Resource'),
    ]

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='unit_resources/', null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    is_required = models.BooleanField(default=False)

    class Meta:
        ordering = ['unit', 'resource_type', 'title']

    def __str__(self):
        return f"{self.unit.code} - {self.title}"

    def clean(self):
        if not self.file and not self.url:
            raise ValidationError('Either a file or URL must be provided.')
        if self.file and self.url:
            raise ValidationError('Only one of file or URL should be provided, not both.')