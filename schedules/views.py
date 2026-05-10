from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from notes.models import SessionNote

from .forms import ScheduleForm
from .models import Schedule
from .services import create_schedule_batch, update_schedule_scope


@login_required
def calendar_view(request):
    upcoming = Schedule.objects.select_related("student", "service_plan").order_by("start_at")[:10]
    return render(request, "schedules/calendar.html", {"upcoming": upcoming})


@login_required
def calendar_events(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    queryset = Schedule.objects.select_related("student", "service_plan", "owner")
    if start:
        queryset = queryset.filter(start_at__gte=datetime.fromisoformat(start.replace("Z", "+00:00")))
    if end:
        queryset = queryset.filter(start_at__lte=datetime.fromisoformat(end.replace("Z", "+00:00")))
    events = [
        {
            "id": schedule.pk,
            "title": schedule.title or f"{schedule.student.name} - {schedule.service_plan.subject}",
            "start": schedule.start_at.isoformat(),
            "end": schedule.end_at.isoformat(),
            "url": reverse("schedules:update", args=[schedule.pk]),
            "backgroundColor": schedule.calendar_color,
            "borderColor": schedule.calendar_color,
            "extendedProps": {
                "student": schedule.student.name,
                "status": schedule.get_status_display(),
                "service_plan": str(schedule.service_plan),
            },
        }
        for schedule in queryset
    ]
    return JsonResponse(events, safe=False)


@login_required
def schedule_create_view(request):
    initial = {}
    if request.method == "GET":
        if request.GET.get("student"):
            initial["student"] = request.GET.get("student")
        if request.GET.get("service_plan"):
            initial["service_plan"] = request.GET.get("service_plan")
    form = ScheduleForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        schedules = create_schedule_batch(owner=request.user, cleaned_data=form.cleaned_data.copy())
        messages.success(request, f"已创建 {len(schedules)} 条排课记录。")
        if len(schedules) == 1:
            return redirect("schedules:update", schedules[0].pk)
        return redirect("schedules:calendar")
    return render(request, "schedules/schedule_form.html", {"form": form, "mode": "create"})


@login_required
def schedule_update_view(request, pk: int):
    schedule = get_object_or_404(
        Schedule.objects.select_related("student", "service_plan", "owner"),
        pk=pk,
    )
    form = ScheduleForm(request.POST or None, instance=schedule)
    if request.method == "POST" and form.is_valid():
        updated = update_schedule_scope(schedule, cleaned_data=form.cleaned_data.copy())
        messages.success(request, f"已更新 {len(updated)} 条排课记录。")
        return redirect("schedules:update", schedule.pk)
    return render(
        request,
        "schedules/schedule_form.html",
        {
            "form": form,
            "mode": "update",
            "schedule": schedule,
            "completion": getattr(schedule, "completion", None),
            "notes": SessionNote.objects.filter(schedule=schedule).order_by("-created_at"),
            "now": timezone.now(),
        },
    )
