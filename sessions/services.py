from django.core.exceptions import ValidationError
from django.db import transaction

from students.models import ServicePlan, ZERO_DECIMAL

from .models import LessonSession


def _reverse_previous_effect(plan: ServicePlan, session: LessonSession):
    if plan.settlement_mode != ServicePlan.SettlementMode.PACKAGE:
        return
    if plan.remaining_hours is None:
        plan.remaining_hours = ZERO_DECIMAL
    plan.remaining_hours += session.deducted_hours
    if plan.total_hours is not None and plan.remaining_hours > plan.total_hours:
        plan.remaining_hours = plan.total_hours
    plan.owed_hours = max(ZERO_DECIMAL, plan.owed_hours - session.owed_hours_added)


def _apply_package_effect(plan: ServicePlan, actual_duration_hours):
    remaining_before = plan.remaining_hours or ZERO_DECIMAL
    deducted_hours = actual_duration_hours
    owed_hours_added = ZERO_DECIMAL
    if remaining_before >= deducted_hours:
        plan.remaining_hours = remaining_before - deducted_hours
    else:
        plan.remaining_hours = ZERO_DECIMAL
        owed_hours_added = deducted_hours - remaining_before
    plan.owed_hours += owed_hours_added
    return deducted_hours, plan.remaining_hours, owed_hours_added


@transaction.atomic
def upsert_completion(*, schedule, attendance_status: str, actual_duration_hours, operator):
    if schedule.status == schedule.Status.CANCELED:
        raise ValidationError("已取消的排课不能被标记为已完成。")

    service_plan = schedule.service_plan
    completion = getattr(schedule, "completion", None)

    if completion:
        _reverse_previous_effect(service_plan, completion)

    deducted_hours = ZERO_DECIMAL
    remaining_hours_after = service_plan.remaining_hours
    owed_hours_added = ZERO_DECIMAL

    if service_plan.settlement_mode == ServicePlan.SettlementMode.PACKAGE:
        deducted_hours, remaining_hours_after, owed_hours_added = _apply_package_effect(
            service_plan,
            actual_duration_hours,
        )
        service_plan.save(update_fields=["remaining_hours", "owed_hours", "updated_at"])

    schedule.status = schedule.Status.COMPLETED
    schedule.save(update_fields=["status", "updated_at"])

    if completion is None:
        completion = LessonSession(schedule=schedule)

    completion.attendance_status = attendance_status
    completion.actual_duration_hours = actual_duration_hours
    completion.deducted_hours = deducted_hours
    completion.remaining_hours_after = remaining_hours_after
    completion.owed_hours_added = owed_hours_added
    completion.operator = operator
    completion.full_clean()
    completion.save()
    return completion
