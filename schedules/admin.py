from django.contrib import admin

from .models import Schedule


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "student",
        "service_plan",
        "owner",
        "start_at",
        "duration_hours",
        "status",
        "delivery_mode",
    )
    search_fields = ("title", "student__name", "student__phone", "service_plan__subject")
    list_filter = ("status", "delivery_mode", "owner")
    autocomplete_fields = ("student", "service_plan", "owner")
