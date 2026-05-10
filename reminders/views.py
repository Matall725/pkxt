from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReminderConfigForm
from .models import ReminderConfig, ReminderTask
from .services import mark_reminder_done, scan_course_reminders, scan_receivable_reminders


@login_required
def reminder_center_view(request):
    config = ReminderConfig.load()
    form = ReminderConfigForm(request.POST or None, instance=config)
    if request.method == "POST" and request.POST.get("action") == "save-config" and form.is_valid():
        form.save()
        messages.success(request, "提醒配置已保存。")
        return redirect("reminders:center")

    tasks = ReminderTask.objects.select_related("content_type").order_by("status", "remind_at")
    return render(request, "reminders/center.html", {"form": form, "tasks": tasks})


@login_required
def reminder_done_view(request, pk: int):
    task = get_object_or_404(ReminderTask, pk=pk)
    if request.method == "POST":
        mark_reminder_done(task)
        messages.success(request, "提醒已标记为完成。")
    return redirect("reminders:center")


@login_required
def reminder_scan_view(request):
    if request.method == "POST":
        created_courses = scan_course_reminders()
        created_receivables = scan_receivable_reminders()
        messages.success(request, f"提醒扫描完成，新增课程提醒 {created_courses} 条，新增待收款提醒 {created_receivables} 条。")
    return redirect("reminders:center")
