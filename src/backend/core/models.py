from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .base_models import BaseModel

User = settings.AUTH_USER_MODEL


class UnitAwareModel(BaseModel):
    """Abstract model providing optional link to Unit and SemesterOffering."""
    class Meta:
        abstract = True


class Event(UnitAwareModel):
    VISIBILITY_CHOICES = (
        ('public', 'Public'),
        ('unit', 'Unit only'),
        ('staff', 'Staff only'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    attendees = models.ManyToManyField(User, related_name='events_attending', blank=True)

    # Targeting: students, class offerings, and intake cohorts
    target_students = models.ManyToManyField(User, related_name='targeted_events', blank=True)
    target_offerings = models.ManyToManyField('academic.SemesterOffering', related_name='targeted_events', blank=True)
    # Intake will be defined below
    target_intakes = models.ManyToManyField('academic.Intake', related_name='targeted_events', blank=True)
    target_all_students = models.BooleanField(default=False,
                                              help_text='If set, event is sent to all students regardless of other targets')

    # Optional relations (importing lazily to avoid circular import issues)
    related_unit = models.ForeignKey('academic.Unit', null=True, blank=True, on_delete=models.SET_NULL)
    related_offering = models.ForeignKey('academic.SemesterOffering', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.title} ({self.start})"

    # Generated content fields (scaffold for GenAI & n8n integration)
    # Stores generated snippets for different channels (social, email, article, ad)
    generated_content = models.JSONField(default=dict, blank=True)
    # generation status: idle, pending, ready, failed
    generation_status = models.CharField(max_length=20, default='idle')
    # metadata about the last generation (tone, brand_score, bias_flag, source)
    generation_meta = models.JSONField(default=dict, blank=True)
    last_generated_at = models.DateTimeField(null=True, blank=True)

    def get_targeted_students(self):
        """Return queryset of students targeted by this event."""
        UserModel = get_user_model()
        
        if self.target_all_students:
            return UserModel.objects.filter(user_type='student', is_active=True)

        qs = UserModel.objects.none()
        if self.target_students.exists():
            qs = qs | self.target_students.all()
        if self.target_offerings.exists():
            qs = qs | UserModel.objects.filter(enrollments__offering__in=self.target_offerings.all())
        if self.target_intakes.exists():
            qs = qs | UserModel.objects.filter(
                enrollments__offering__intake__in=self.target_intakes.all()
            )
        return qs.distinct()




class Session(BaseModel):
    SESSION_TYPES = (
        ('lecture', 'Lecture'),
        ('tutorial', 'Tutorial'),
        ('lab', 'Lab'),
        ('other', 'Other'),
    )
    unit = models.ForeignKey('academic.Unit', on_delete=models.CASCADE)
    offering = models.ForeignKey('academic.SemesterOffering', null=True, blank=True, on_delete=models.SET_NULL)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='lecture')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    instructor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='sessions_instructing')

    def __str__(self):
        return f"{self.unit} {self.session_type} @ {self.date} {self.start_time}"


class AttendanceRecord(BaseModel):
    STATUS = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    )
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=20, choices=STATUS, default='present')
    marked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='attendance_marked')
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student} - {self.session} : {self.status}"


class Ticket(BaseModel):
    PRIORITY_CHOICES = (('low', 'Low'), ('medium', 'Medium'), ('high', 'High'))
    STATUS_CHOICES = (('open', 'Open'), ('in_progress', 'In Progress'), ('closed', 'Closed'))

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    submitter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets_submitted')
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='tickets_assigned')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=100, blank=True)

    related_unit = models.ForeignKey('academic.Unit', null=True, blank=True, on_delete=models.SET_NULL)
    related_offering = models.ForeignKey('academic.SemesterOffering', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"[{self.status}] {self.title}"


class TicketComment(BaseModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()

    def __str__(self):
        return f"Comment by {self.commenter} on {self.ticket}"


class Form(BaseModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    schema = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class FormSubmission(BaseModel):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='submissions')
    submitter = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    data = models.JSONField(default=dict)

    def __str__(self):
        return f"Submission {self.pk} for {self.form.name}"


class Notification(BaseModel):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='notifications_sent')
    verb = models.CharField(max_length=200)
    target_content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')
    unread = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification to {self.recipient}: {self.verb}"


class Resource(BaseModel):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='resources/')
    unit = models.ForeignKey('academic.Unit', null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.title


class Page(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(blank=True)
    unit = models.ForeignKey('academic.Unit', null=True, blank=True, on_delete=models.SET_NULL)
    published = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class MediaAsset(BaseModel):
    file = models.FileField(upload_to='media_assets/')
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"MediaAsset {self.pk}"
