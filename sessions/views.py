from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from schedules.models import Schedule

from .forms import LessonSessionForm
from .services import upsert_completion


@login_required
def complete_schedule_view(request, schedule_id: int):
    schedule = get_object_or_404(Schedule.objects.select_related("student", "service_plan"), pk=schedule_id)
    completion = getattr(schedule, "completion", None)
    form = LessonSessionForm(
        request.POST or None,
        instance=completion,
        initial={"actual_duration_hours": completion.actual_duration_hours if completion else schedule.duration_hours},
    )
    if request.method == "POST" and form.is_valid():
        upsert_completion(
            schedule=schedule,
            attendance_status=form.cleaned_data["attendance_status"],
            actual_duration_hours=form.cleaned_data["actual_duration_hours"],
            operator=request.user,
        )
        messages.success(request, "课程完成记录已保存。")
        return redirect("schedules:update", schedule.pk)
    return render(request, "sessions/complete_form.html", {"form": form, "schedule": schedule})
