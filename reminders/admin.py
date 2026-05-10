from django.contrib import admin

from .models import ReminderConfig, ReminderTask


@admin.register(ReminderTask)
class ReminderTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "reminder_type", "status", "remind_at", "created_at")
    search_fields = ("title", "message", "window_key")
    list_filter = ("reminder_type", "status")


@admin.register(ReminderConfig)
class ReminderConfigAdmin(admin.ModelAdmin):
    list_display = ("course_enabled", "course_lead_minutes", "receivable_enabled", "receivable_due_offset_days")
