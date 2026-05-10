from datetime import timedelta
from uuid import uuid4

from django.db import transaction

from .forms import ScheduleForm
from .models import Schedule


def build_recurrence_rule(frequency: str, interval: int, count: int) -> str:
    if frequency == ScheduleForm.RepeatFrequency.NONE or count <= 1:
        return ""
    return f"FREQ={frequency.upper()};INTERVAL={interval};COUNT={count}"


def generate_occurrences(start_at, frequency: str, interval: int, count: int):
    current = start_at
    for _ in range(count):
        yield current
        if frequency == ScheduleForm.RepeatFrequency.DAILY:
            current = current + timedelta(days=interval)
        elif frequency == ScheduleForm.RepeatFrequency.WEEKLY:
            current = current + timedelta(weeks=interval)


@transaction.atomic
def create_schedule_batch(*, owner, cleaned_data: dict):
    repeat_frequency = cleaned_data.pop("repeat_frequency")
    repeat_interval = cleaned_data.pop("repeat_interval")
    repeat_count = cleaned_data.pop("repeat_count")
    cleaned_data.pop("update_scope", None)
    base_start_at = cleaned_data.pop("start_at")

    recurrence_rule = build_recurrence_rule(repeat_frequency, repeat_interval, repeat_count)
    recurrence_group = uuid4() if recurrence_rule else None
    schedules = []

    for start_at in generate_occurrences(
        base_start_at,
        repeat_frequency,
        repeat_interval,
        repeat_count,
    ):
        schedule = Schedule(
            **cleaned_data,
            owner=owner,
            start_at=start_at,
            recurrence_group=recurrence_group,
            recurrence_rule=recurrence_rule,
        )
        schedule.full_clean()
        schedule.save()
        schedules.append(schedule)
    return schedules


@transaction.atomic
def update_schedule_scope(schedule: Schedule, *, cleaned_data: dict):
    scope = cleaned_data.pop("update_scope", ScheduleForm.Scope.SINGLE)
    cleaned_data.pop("repeat_frequency", None)
    cleaned_data.pop("repeat_interval", None)
    cleaned_data.pop("repeat_count", None)

    if scope == ScheduleForm.Scope.SINGLE or not schedule.recurrence_group:
        targets = [schedule]
    else:
        queryset = Schedule.objects.filter(recurrence_group=schedule.recurrence_group).order_by("start_at", "id")
        if scope == ScheduleForm.Scope.FUTURE:
            queryset = queryset.filter(start_at__gte=schedule.start_at)
        targets = list(queryset)

    delta = cleaned_data["start_at"] - schedule.start_at
    updated = []
    for item in targets:
        item.student = cleaned_data["student"]
        item.service_plan = cleaned_data["service_plan"]
        item.title = cleaned_data["title"]
        item.duration_hours = cleaned_data["duration_hours"]
        item.status = cleaned_data["status"]
        item.delivery_mode = cleaned_data["delivery_mode"]
        item.location = cleaned_data["location"]
        if len(targets) == 1:
            item.start_at = cleaned_data["start_at"]
        else:
            item.start_at = item.start_at + delta
        item.full_clean()
        item.save()
        updated.append(item)
    return updated
