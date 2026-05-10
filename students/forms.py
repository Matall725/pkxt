from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import ServicePlan, Student


def apply_bootstrap_classes(form):
    for field in form.fields.values():
        widget = field.widget
        current = widget.attrs.get("class", "")
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = f"{current} form-check-input".strip()
            continue
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            widget.attrs["class"] = f"{current} form-select".strip()
        else:
            widget.attrs["class"] = f"{current} form-control".strip()


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "name",
            "nickname",
            "gender",
            "age",
            "phone",
            "parent_phone",
            "tags",
            "source_channel",
            "status",
            "service_type",
            "risk_flag",
            "attention_note",
        ]
        widgets = {
            "age": forms.NumberInput(attrs={"min": "0"}),
            "attention_note": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "name": "姓名",
            "nickname": "昵称",
            "gender": "性别",
            "age": "年龄",
            "phone": "手机号",
            "parent_phone": "家长联系方式",
            "tags": "标签",
            "source_channel": "来源渠道",
            "status": "状态",
            "service_type": "服务类型",
            "risk_flag": "风险标记",
            "attention_note": "重点关注",
        }
        help_texts = {
            "tags": "使用逗号分隔多个标签",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self)


class ServicePlanForm(forms.ModelForm):
    class Meta:
        model = ServicePlan
        fields = [
            "subject",
            "settlement_mode",
            "unit_price",
            "total_hours",
            "remaining_hours",
            "owed_hours",
            "effective_from",
            "expires_at",
            "is_active",
        ]
        widgets = {
            "unit_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "total_hours": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "remaining_hours": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "owed_hours": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "effective_from": forms.DateInput(attrs={"type": "date"}),
            "expires_at": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "subject": "科目/咨询类型",
            "settlement_mode": "结算模式",
            "unit_price": "单价",
            "total_hours": "总课时",
            "remaining_hours": "剩余课时",
            "owed_hours": "欠课时",
            "effective_from": "生效日期",
            "expires_at": "失效日期",
            "is_active": "当前生效",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self)


class BaseServicePlanFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_count = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or not form.cleaned_data:
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            if form.cleaned_data.get("is_active"):
                active_count += 1
        if active_count > 1:
            raise forms.ValidationError("同一学员只能保留一个生效中的服务方案。")


ServicePlanFormSet = inlineformset_factory(
    Student,
    ServicePlan,
    form=ServicePlanForm,
    formset=BaseServicePlanFormSet,
    extra=1,
    can_delete=True,
)
