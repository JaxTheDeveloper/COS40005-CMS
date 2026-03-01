from django.contrib import admin
from . import models


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start', 'end', 'created_by', 'visibility', 'target_all_students')
    search_fields = ('title', 'description')
    filter_horizontal = ('attendees', 'target_students', 'target_offerings', 'target_intakes')
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'start', 'end', 'location', 'visibility'),
        }),
        ('Relations', {
            'fields': ('created_by', 'related_unit', 'related_offering'),
        }),
        ('Attendance', {
            'fields': ('attendees',),
        }),
        ('Targeting', {
            'fields': ('target_all_students', 'target_students', 'target_offerings', 'target_intakes'),
            'description': 'Granular control over who receives this event notification.',
        }),
        ('Generated Content', {
            'fields': ('generated_content', 'generation_status', 'generation_meta', 'last_generated_at'),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'deleted_at', 'is_deleted'),
            'classes': ('collapse',),
        }),
    )


@admin.register(models.Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('unit', 'session_type', 'date', 'start_time')
    list_filter = ('session_type',)


@admin.register(models.AttendanceRecord)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('session', 'student', 'status', 'created_at')
    search_fields = ('student__email',)


@admin.register(models.Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'submitter', 'assigned_to')
    list_filter = ('status', 'priority')


@admin.register(models.TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'commenter', 'created_at')


@admin.register(models.Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_by', 'is_active')


@admin.register(models.FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ('form', 'submitter', 'created_at')


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'verb', 'unread', 'created_at')


@admin.register(models.Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'uploaded_by', 'created_at')


@admin.register(models.Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'unit', 'published')


@admin.register(models.MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('pk', 'uploaded_by', 'created_at')


from src.backend.academic.models import Intake

@admin.register(Intake)
class IntakeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'semester', 'year')
    list_filter = ('year', 'semester')
    ordering = ['-year', 'semester']

