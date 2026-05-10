from django import forms
from django.utils import timezone

from students.models import ServicePlan, Student

from .models import PaymentEntry, Receivable


class ReceivableForm(forms.ModelForm):
    class Meta:
        model = Receivable
        fields = ["student", "service_plan", "title", "amount_due", "issue_date", "due_date", "note"]
        widgets = {
            "amount_due": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "issue_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields["student"].queryset = Student.objects.order_by("name", "id")
        student_id = self.data.get("student") or self.initial.get("student") or getattr(self.instance, "student_id", None)
        queryset = ServicePlan.objects.select_related("student").order_by("-is_active", "-effective_from", "-id")
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        self.fields["service_plan"].queryset = queryset
        self.fields["issue_date"].initial = self.fields["issue_date"].initial or today
        self.fields["due_date"].initial = self.fields["due_date"].initial or today


class PaymentEntryForm(forms.ModelForm):
    class Meta:
        model = PaymentEntry
        fields = ["amount", "method", "received_at", "note"]
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "received_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }
