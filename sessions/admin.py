from django.contrib import admin

from .models import LessonSession


@admin.register(LessonSession)
class LessonSessionAdmin(admin.ModelAdmin):
    list_display = (
        "schedule",
        "attendance_status",
        "actual_duration_hours",
        "deducted_hours",
        "owed_hours_added",
        "operator",
        "created_at",
    )
    search_fields = ("schedule__student__name", "schedule__student__phone")
    list_filter = ("attendance_status",)
    autocomplete_fields = ("schedule", "operator")
