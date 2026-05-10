from django import forms

from .models import SessionNote


class SessionNoteForm(forms.ModelForm):
    class Meta:
        model = SessionNote
        fields = ["summary", "next_focus", "internal_note"]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 4}),
            "next_focus": forms.Textarea(attrs={"rows": 3}),
            "internal_note": forms.Textarea(attrs={"rows": 3}),
        }
