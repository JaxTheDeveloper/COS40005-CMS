from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class UnitAwareModel(models.Model):
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
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='events_created')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    attendees = models.ManyToManyField(User, related_name='events_attending', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional relations (importing lazily to avoid circular import issues)
    related_unit = models.ForeignKey('academic.Unit', null=True, blank=True, on_delete=models.SET_NULL)
    related_offering = models.ForeignKey('academic.SemesterOffering', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.title} ({self.start})"


class Session(models.Model):
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


class AttendanceRecord(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student} - {self.session} : {self.status}"


class Ticket(models.Model):
    PRIORITY_CHOICES = (('low', 'Low'), ('medium', 'Medium'), ('high', 'High'))
    STATUS_CHOICES = (('open', 'Open'), ('in_progress', 'In Progress'), ('closed', 'Closed'))

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    submitter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets_submitted')
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='tickets_assigned')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    related_unit = models.ForeignKey('academic.Unit', null=True, blank=True, on_delete=models.SET_NULL)
    related_offering = models.ForeignKey('academic.SemesterOffering', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"[{self.status}] {self.title}"


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.commenter} on {self.ticket}"


class Form(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    schema = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FormSubmission(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='submissions')
    submitter = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    data = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission {self.pk} for {self.form.name}"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='notifications_sent')
    verb = models.CharField(max_length=200)
    target_content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')
    unread = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.recipient}: {self.verb}"


class Resource(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='resources/')
    unit = models.ForeignKey('academic.Unit', null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Page(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(blank=True)
    unit = models.ForeignKey('academic.Unit', null=True, blank=True, on_delete=models.SET_NULL)
    published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class MediaAsset(models.Model):
    file = models.FileField(upload_to='media_assets/')
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"MediaAsset {self.pk}"
