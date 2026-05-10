from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import PaymentEntryForm, ReceivableForm
from .models import Receivable


@login_required
def receivable_list_view(request):
    status = request.GET.get("status", "")
    search = request.GET.get("search", "").strip()
    queryset = Receivable.objects.select_related("student", "service_plan").prefetch_related("entries")
    if status:
        queryset = queryset.filter(status=status)
    if search:
        queryset = queryset.filter(Q(student__name__icontains=search) | Q(title__icontains=search))
    totals = queryset.aggregate(
        total_due=Sum("amount_due"),
        total_received=Sum("amount_received"),
    )
    return render(
        request,
        "payments/receivable_list.html",
        {
            "receivables": queryset.order_by("status", "due_date"),
            "selected_status": status,
            "search": search,
            "totals": totals,
        },
    )


@login_required
def receivable_create_view(request):
    initial = {}
    if request.method == "GET":
        if request.GET.get("student"):
            initial["student"] = request.GET.get("student")
        if request.GET.get("service_plan"):
            initial["service_plan"] = request.GET.get("service_plan")
    form = ReceivableForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        receivable = form.save(commit=False)
        receivable.created_by = request.user
        receivable.full_clean()
        receivable.save()
        messages.success(request, "应收记录已创建。")
        return redirect("payments:list")
    return render(request, "payments/receivable_form.html", {"form": form, "mode": "create"})


@login_required
def receivable_update_view(request, pk: int):
    receivable = get_object_or_404(Receivable.objects.select_related("student", "service_plan"), pk=pk)
    form = ReceivableForm(request.POST or None, instance=receivable)
    if request.method == "POST" and form.is_valid():
        receivable = form.save(commit=False)
        receivable.full_clean()
        receivable.save()
        messages.success(request, "应收记录已更新。")
        return redirect("payments:update", receivable.pk)
    return render(
        request,
        "payments/receivable_form.html",
        {
            "form": form,
            "mode": "update",
            "receivable": receivable,
            "entry_form": PaymentEntryForm(
                initial={"received_at": timezone.localtime().strftime("%Y-%m-%dT%H:%M")},
            ),
        },
    )


@login_required
def payment_entry_create_view(request, receivable_id: int):
    receivable = get_object_or_404(Receivable, pk=receivable_id)
    form = PaymentEntryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        entry.receivable = receivable
        entry.created_by = request.user
        entry.save()
        messages.success(request, "实收流水已记录。")
        return redirect("payments:update", receivable.pk)
    return render(request, "payments/payment_entry_form.html", {"form": form, "receivable": receivable})
