import logging
from datetime import datetime, time, timedelta

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from payments.models import Receivable
from schedules.models import Schedule

from .models import ReminderConfig, ReminderTask


logger = logging.getLogger(__name__)


@transaction.atomic
def scan_course_reminders(now=None):
    now = now or timezone.now()
    config = ReminderConfig.load()
    if not config.course_enabled:
        return 0

    lead_delta = timedelta(minutes=config.course_lead_minutes)
    upper_bound = now + lead_delta
    created_count = 0
    queryset = Schedule.objects.select_related("student").filter(
        status__in=[Schedule.Status.PENDING, Schedule.Status.RESCHEDULED],
        start_at__gte=now,
        start_at__lte=upper_bound,
    )
    content_type = ContentType.objects.get_for_model(Schedule)
    for schedule in queryset:
        window_key = f"course:{schedule.pk}:{schedule.start_at.isoformat()}:{config.course_lead_minutes}"
        task, created = ReminderTask.objects.get_or_create(
            window_key=window_key,
            defaults={
                "content_type": content_type,
                "object_id": schedule.pk,
                "reminder_type": ReminderTask.ReminderType.COURSE,
                "remind_at": schedule.start_at - lead_delta,
                "title": f"课程提醒：{schedule.student.name}",
                "message": f"{schedule.student.name} 的课程将在 {timezone.localtime(schedule.start_at).strftime('%Y-%m-%d %H:%M')} 开始。",
            },
        )
        if created:
            created_count += 1
            logger.info("Created course reminder %s", task.window_key)
    return created_count


@transaction.atomic
def scan_receivable_reminders(today=None):
    today = today or timezone.localdate()
    config = ReminderConfig.load()
    if not config.receivable_enabled:
        return 0

    due_limit = today + timedelta(days=config.receivable_due_offset_days)
    created_count = 0
    queryset = Receivable.objects.select_related("student").filter(
        status__in=[Receivable.Status.PENDING, Receivable.Status.PARTIAL],
        due_date__lte=due_limit,
    )
    content_type = ContentType.objects.get_for_model(Receivable)
    for receivable in queryset:
        window_key = f"receivable:{receivable.pk}:{receivable.due_date.isoformat()}:{config.receivable_due_offset_days}"
        task, created = ReminderTask.objects.get_or_create(
            window_key=window_key,
            defaults={
                "content_type": content_type,
                "object_id": receivable.pk,
                "reminder_type": ReminderTask.ReminderType.RECEIVABLE,
                "remind_at": timezone.make_aware(datetime.combine(receivable.due_date, time.min)),
                "title": f"待收款提醒：{receivable.student.name}",
                "message": f"{receivable.student.name} 的 {receivable.title} 尚未结清，到期日为 {receivable.due_date:%Y-%m-%d}。",
            },
        )
        if created:
            created_count += 1
            logger.info("Created receivable reminder %s", task.window_key)
    return created_count


def mark_reminder_done(task: ReminderTask):
    task.status = ReminderTask.Status.DONE
    task.completed_at = timezone.now()
    task.save(update_fields=["status", "completed_at", "updated_at"])
    return task
