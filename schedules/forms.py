from django import forms
from django.core.exceptions import ValidationError
from django.db import models

from students.models import ServicePlan, Student

from .models import Schedule


class ScheduleForm(forms.ModelForm):
    class RepeatFrequency(models.TextChoices):
        NONE = "none", "不重复"
        DAILY = "daily", "每天"
        WEEKLY = "weekly", "每周"

    class Scope(models.TextChoices):
        SINGLE = "single", "仅本次"
        FUTURE = "future", "本次及未来"
        SERIES = "series", "整个系列"

    repeat_frequency = forms.ChoiceField(label="重复规则", choices=RepeatFrequency.choices, initial=RepeatFrequency.NONE)
    repeat_interval = forms.IntegerField(label="重复间隔", min_value=1, initial=1)
    repeat_count = forms.IntegerField(label="重复次数", min_value=1, initial=1)
    update_scope = forms.ChoiceField(label="修改范围", choices=Scope.choices, initial=Scope.SINGLE, required=False)

    class Meta:
        model = Schedule
        fields = [
            "student",
            "service_plan",
            "title",
            "start_at",
            "duration_hours",
            "status",
            "delivery_mode",
            "location",
        ]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "duration_hours": forms.NumberInput(attrs={"step": "0.25", "min": "0.25"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.order_by("name", "id")
        student_id = self.data.get("student") or self.initial.get("student") or getattr(self.instance, "student_id", None)
        queryset = ServicePlan.objects.select_related("student").order_by("-is_active", "-effective_from", "-id")
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        self.fields["service_plan"].queryset = queryset
        if self.instance.pk and self.instance.recurrence_rule:
            segments = {}
            for part in self.instance.recurrence_rule.split(";"):
                if "=" in part:
                    key, value = part.split("=", 1)
                    segments[key] = value
            self.fields["repeat_frequency"].initial = segments.get("FREQ", "NONE").lower()
            self.fields["repeat_interval"].initial = int(segments.get("INTERVAL", 1))
            self.fields["repeat_count"].initial = int(segments.get("COUNT", 1))
        self.fields["student"].label_from_instance = lambda student: f"{student.name}（{student.phone}）"

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        service_plan = cleaned_data.get("service_plan")
        if student and service_plan and service_plan.student_id != student.id:
            raise ValidationError("服务方案必须属于当前学员。")
        if cleaned_data.get("repeat_frequency") == self.RepeatFrequency.NONE:
            cleaned_data["repeat_count"] = 1
        return cleaned_data
