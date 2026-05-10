from django import forms

from .models import ReminderConfig


class ReminderConfigForm(forms.ModelForm):
    class Meta:
        model = ReminderConfig
        fields = [
            "course_enabled",
            "course_lead_minutes",
            "receivable_enabled",
            "receivable_due_offset_days",
        ]
