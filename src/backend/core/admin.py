from django.contrib import admin
from . import models


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start', 'end', 'created_by', 'visibility')
    search_fields = ('title', 'description')


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
    list_display = ('form', 'submitter', 'submitted_at')


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
