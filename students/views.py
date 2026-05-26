from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ServicePlanFormSet, StudentForm
from .models import Student


def _ordered_plans_from_formset(formset):
    changed_existing = []
    new_instances = []
    for form in formset.forms:
        if not hasattr(form, "cleaned_data") or not form.cleaned_data:
            continue
        if form.cleaned_data.get("DELETE") or not form.has_changed():
            continue
        instance = form.save(commit=False)
        if instance.pk:
            changed_existing.append(instance)
        else:
            new_instances.append(instance)
    changed_existing.sort(key=lambda plan: (plan.is_active, plan.pk or 0))
    new_instances.sort(key=lambda plan: plan.is_active)
    return changed_existing, new_instances


def _build_student_form_bundle(request, instance=None):
    form = StudentForm(request.POST or None, instance=instance)
    formset = ServicePlanFormSet(request.POST or None, instance=instance, prefix="plans")
    return form, formset


def _save_student_bundle(request, form, formset):
    student = form.save(commit=False)
    if not student.owner_id:
        student.owner = request.user

    with transaction.atomic():
        student.full_clean()
        student.save()

        formset.instance = student
        for deleted_form in formset.deleted_forms:
            if deleted_form.instance.pk:
                deleted_form.instance.delete()

        changed_existing, new_instances = _ordered_plans_from_formset(formset)
        for plan in changed_existing:
            plan.student = student
            plan.full_clean()
            plan.save()
        for plan in new_instances:
            plan.student = student
            plan.full_clean()
            plan.save()
    return student


@login_required
def student_list_view(request):
    status = request.GET.get("status", "").strip()
    search = request.GET.get("search", "").strip()
    status_choices = [
        (Student.Status.ACTIVE, "服务中"),
        (Student.Status.LEAD, "潜在"),
        (Student.Status.PAUSED, "暂停"),
        (Student.Status.CLOSED, "结束"),
    ]

    queryset = (
        Student.objects.prefetch_related("service_plans")
        .annotate(
            schedule_count=Count("schedules", distinct=True),
            receivable_count=Count("receivables", distinct=True),
            note_count=Count("notes", distinct=True),
        )
        .order_by("-updated_at", "-id")
    )
    if status:
        queryset = queryset.filter(status=status)
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(nickname__icontains=search)
            | Q(phone__icontains=search)
            | Q(parent_phone__icontains=search)
        )

    base_queryset = Student.objects.all()
    totals = {
        "all": base_queryset.count(),
        "active": base_queryset.filter(status=Student.Status.ACTIVE).count(),
        "lead": base_queryset.filter(status=Student.Status.LEAD).count(),
        "paused": base_queryset.filter(status=Student.Status.PAUSED).count(),
    }
    return render(
        request,
        "students/student_list.html",
        {
            "students": queryset,
            "search": search,
            "selected_status": status,
            "totals": totals,
            "status_choices": status_choices,
        },
    )


@login_required
def student_create_view(request):
    form, formset = _build_student_form_bundle(request)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        student = _save_student_bundle(request, form, formset)
        messages.success(request, "学员档案已创建。")
        return redirect("students:update", student.pk)
    return render(
        request,
        "students/student_form.html",
        {
            "form": form,
            "service_plan_formset": formset,
            "mode": "create",
        },
    )


def calculate_payment_latency(student):
    today = timezone.localdate()
    receivables = student.receivables.all()
    if not receivables.exists():
        return 0.0

    total_latency_days = 0
    count = 0
    for r in receivables:
        if r.status == "paid":
            latest_entry = r.entries.order_by("-received_at").first()
            if latest_entry:
                actual_date = timezone.localtime(latest_entry.received_at).date()
                latency = (actual_date - r.due_date).days
                if latency > 0:
                    total_latency_days += latency
                    count += 1
        else:
            if r.due_date < today:
                latency = (today - r.due_date).days
                total_latency_days += latency
                count += 1

    return round(total_latency_days / count, 1) if count > 0 else 0.0


@login_required
def student_update_view(request, pk: int):
    student = get_object_or_404(Student.objects.prefetch_related("service_plans"), pk=pk)
    form, formset = _build_student_form_bundle(request, instance=student)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        student = _save_student_bundle(request, form, formset)
        messages.success(request, "学员档案已更新。")
        return redirect("students:update", student.pk)

    recent_schedules = student.schedules.select_related("service_plan").order_by("-start_at")[:8]
    receivables = student.receivables.select_related("service_plan").prefetch_related("entries").order_by("-due_date")[:8]
    recent_notes = student.notes.select_related("schedule").order_by("-created_at")[:6]
    receivable_totals = student.receivables.aggregate(
        amount_due=Coalesce(Sum("amount_due"), Decimal("0")),
        amount_received=Coalesce(Sum("amount_received"), Decimal("0")),
    )
    outstanding = receivable_totals["amount_due"] - receivable_totals["amount_received"]

    # 计算风险指标
    total_schedules = student.schedules.count()
    canceled_schedules = student.schedules.filter(status="canceled").count()
    cancellation_rate = round((canceled_schedules / total_schedules * 100), 1) if total_schedules > 0 else 0.0

    payment_latency = calculate_payment_latency(student)

    active_plan = student.active_service_plan
    remaining_hours = active_plan.remaining_hours if (active_plan and active_plan.remaining_hours is not None) else Decimal("0")

    summary = {
        "schedule_count": student.schedules.count(),
        "note_count": student.notes.count(),
        "receivable_due": receivable_totals["amount_due"],
        "receivable_received": receivable_totals["amount_received"],
        "receivable_outstanding": outstanding if outstanding > Decimal("0") else Decimal("0"),
        "cancellation_rate": cancellation_rate,
        "payment_latency": payment_latency,
        "remaining_hours": remaining_hours,
    }
    return render(
        request,
        "students/student_form.html",
        {
            "form": form,
            "service_plan_formset": formset,
            "mode": "update",
            "student": student,
            "recent_schedules": recent_schedules,
            "receivables": receivables,
            "recent_notes": recent_notes,
            "summary": summary,
        },
    )
