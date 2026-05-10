from django import forms

from .models import LessonSession


class LessonSessionForm(forms.ModelForm):
    class Meta:
        model = LessonSession
        fields = ["attendance_status", "actual_duration_hours"]
        widgets = {
            "actual_duration_hours": forms.NumberInput(attrs={"step": "0.25", "min": "0"}),
        }
