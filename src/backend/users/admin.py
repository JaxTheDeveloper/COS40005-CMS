from django.contrib import admin
from . import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'user_type', 'is_active', 'is_staff')
    search_fields = ('email', 'username')
    list_filter = ('user_type', 'is_staff', 'is_active')


@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(models.UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'valid_from', 'valid_until')
    search_fields = ('user__email', 'role__name')


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'duration_years', 'is_active')
    search_fields = ('code', 'name')


@admin.register(models.Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'convenor', 'is_active')
    search_fields = ('code', 'name')


@admin.register(models.StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'user', 'course', 'academic_status')
    search_fields = ('student_id', 'user__email')


@admin.register(models.ParentGuardian)
class ParentGuardianAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__email',)


@admin.register(models.Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'unit', 'semester', 'year', 'status')
    search_fields = ('student__email', 'unit__code')


@admin.register(models.Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'is_active')
    search_fields = ('name',)


@admin.register(models.ScholarshipApplication)
class ScholarshipApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'scholarship', 'status', 'application_date')
    search_fields = ('student__email', 'scholarship__name')


@admin.register(models.AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'resource_type')
    search_fields = ('user__email', 'action', 'resource_type')


@admin.register(models.N8NWorkflow)
class N8NWorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'workflow_id', 'trigger_event', 'is_active')
    search_fields = ('name', 'workflow_id')


@admin.register(models.N8NExecutionLog)
class N8NExecutionLogAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'execution_id', 'status', 'start_time')
    search_fields = ('workflow__name', 'execution_id')
