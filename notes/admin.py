from django.contrib import admin

from .models import SessionNote


@admin.register(SessionNote)
class SessionNoteAdmin(admin.ModelAdmin):
    list_display = ("student", "schedule", "created_by", "created_at")
    search_fields = ("student__name", "student__phone", "summary", "next_focus")
    list_filter = ("created_at",)
    autocomplete_fields = ("student", "schedule", "completion", "created_by")
