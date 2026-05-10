from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from students.models import TimeStampedModel, ZERO_DECIMAL


class LessonSession(TimeStampedModel):
    class AttendanceStatus(models.TextChoices):
        PRESENT = "present", "正常出勤"
        PARTIAL = "partial", "部分出勤"
        ABSENT = "absent", "缺勤"
        LEAVE = "leave", "请假"

    schedule = models.OneToOneField(
        "schedules.Schedule",
        verbose_name="排课",
        related_name="completion",
        on_delete=models.CASCADE,
    )
    attendance_status = models.CharField("实际出勤", max_length=16, choices=AttendanceStatus.choices)
    actual_duration_hours = models.DecimalField(
        "实际时长（小时）",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(ZERO_DECIMAL)],
    )
    deducted_hours = models.DecimalField(
        "扣减课时",
        max_digits=8,
        decimal_places=2,
        default=ZERO_DECIMAL,
        validators=[MinValueValidator(ZERO_DECIMAL)],
    )
    remaining_hours_after = models.DecimalField(
        "扣减后剩余课时",
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    owed_hours_added = models.DecimalField(
        "新增欠课时",
        max_digits=8,
        decimal_places=2,
        default=ZERO_DECIMAL,
        validators=[MinValueValidator(ZERO_DECIMAL)],
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="操作人",
        related_name="lesson_sessions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-schedule__start_at"]
        verbose_name = "完成记录"
        verbose_name_plural = "完成记录"

    def clean(self):
        if self.schedule_id and self.schedule.status != self.schedule.Status.COMPLETED:
            raise ValidationError({"schedule": "只有已完成的排课才能拥有完成记录。"})

    def __str__(self) -> str:
        return f"{self.schedule.student.name} - 完成记录"
