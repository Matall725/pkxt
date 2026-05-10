from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from schedules.models import Schedule

from .forms import SessionNoteForm
from .models import SessionNote


@login_required
def note_create_view(request, schedule_id: int):
    schedule = get_object_or_404(Schedule.objects.select_related("student"), pk=schedule_id)
    form = SessionNoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        note = form.save(commit=False)
        note.student = schedule.student
        note.schedule = schedule
        note.completion = getattr(schedule, "completion", None)
        note.created_by = request.user
        note.full_clean()
        note.save()
        messages.success(request, "课后备注已保存。")
        return redirect("schedules:update", schedule.pk)
    return render(request, "notes/note_form.html", {"form": form, "schedule": schedule, "mode": "create"})


@login_required
def note_update_view(request, pk: int):
    note = get_object_or_404(SessionNote.objects.select_related("schedule", "student"), pk=pk)
    form = SessionNoteForm(request.POST or None, instance=note)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.student = note.student
        updated.schedule = note.schedule
        updated.completion = note.completion
        updated.full_clean()
        updated.save()
        messages.success(request, "课后备注已更新。")
        return redirect("schedules:update", note.schedule.pk)
    return render(request, "notes/note_form.html", {"form": form, "schedule": note.schedule, "mode": "update"})
