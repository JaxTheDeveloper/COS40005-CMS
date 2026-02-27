from django.contrib import admin
from .models import Course, CourseUnit, Unit, SemesterOffering, UnitResource


class CourseUnitInline(admin.TabularInline):
    model = CourseUnit
    extra = 1
    fields = ('unit', 'is_elective')
    autocomplete_fields = ['unit']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'duration_years', 'is_active')
    search_fields = ('code', 'name', 'department')
    list_filter = ('is_active', 'department')
    inlines = [CourseUnitInline]


@admin.register(CourseUnit)
class CourseUnitAdmin(admin.ModelAdmin):
    list_display = ('course', 'unit', 'is_elective')
    list_filter = ('is_elective', 'course')
    search_fields = ('course__code', 'course__name', 'unit__code', 'unit__name')
    autocomplete_fields = ['course', 'unit']


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'credit_points', 'is_active')
    search_fields = ('code', 'name', 'department')
    list_filter = ('is_active', 'department')
    filter_horizontal = ('prerequisites', 'anti_requisites')


@admin.register(SemesterOffering)
class SemesterOfferingAdmin(admin.ModelAdmin):
    list_display = ('unit', 'year', 'semester', 'capacity', 'current_enrollment', 'is_active')
    list_filter = ('year', 'semester', 'is_active')
    search_fields = ('unit__code', 'unit__name')


@admin.register(UnitResource)
class UnitResourceAdmin(admin.ModelAdmin):
    list_display = ('unit', 'title', 'resource_type', 'is_required')
    list_filter = ('resource_type', 'is_required')
    search_fields = ('unit__code', 'title')
