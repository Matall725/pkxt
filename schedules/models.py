import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from students.models import TimeStampedModel, ZERO_DECIMAL


class Schedule(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "待上课"
        COMPLETED = "completed", "已完成"
        CANCELED = "canceled", "已取消"
        RESCHEDULED = "rescheduled", "已改期"

    class DeliveryMode(models.TextChoices):
        ONLINE = "online", "线上"
        OFFLINE = "offline", "线下"

    student = models.ForeignKey(
        "students.Student",
        verbose_name="学员",
        related_name="schedules",
        on_delete=models.CASCADE,
    )
    service_plan = models.ForeignKey(
        "students.ServicePlan",
        verbose_name="服务方案",
        related_name="schedules",
        on_delete=models.PROTECT,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="执行账号",
        related_name="owned_schedules",
        on_delete=models.PROTECT,
    )
    title = models.CharField("标题", max_length=128, blank=True)
    start_at = models.DateTimeField("开始时间")
    duration_hours = models.DecimalField(
        "时长（小时）",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.25"))],
    )
    status = models.CharField("状态", max_length=16, choices=Status.choices, default=Status.PENDING)
    delivery_mode = models.CharField("上课方式", max_length=16, choices=DeliveryMode.choices, default=DeliveryMode.ONLINE)
    location = models.CharField("地点/链接", max_length=255, blank=True)
    recurrence_group = models.UUIDField("系列分组", null=True, blank=True, db_index=True)
    recurrence_rule = models.CharField("系列规则", max_length=255, blank=True)

    class Meta:
        ordering = ["start_at", "id"]
        verbose_name = "排课"
        verbose_name_plural = "排课"
        indexes = [
            models.Index(fields=["start_at"], name="schedule_start_idx"),
            models.Index(fields=["status"], name="schedule_status_idx"),
            models.Index(fields=["owner", "start_at"], name="schedule_owner_start_idx"),
            models.Index(fields=["student", "start_at"], name="schedule_student_start_idx"),
        ]

    def __str__(self) -> str:
        return self.title or f"{self.student.name} - {timezone.localtime(self.start_at).strftime('%Y-%m-%d %H:%M')}"

    @property
    def end_at(self):
        return self.start_at + timedelta(minutes=int(self.duration_hours * Decimal("60")))

    @property
    def effective_status(self) -> str:
        return self.get_status_display()

    @property
    def calendar_color(self) -> str:
        mapping = {
            self.Status.PENDING: "#2563eb",
            self.Status.COMPLETED: "#16a34a",
            self.Status.CANCELED: "#dc2626",
            self.Status.RESCHEDULED: "#f59e0b",
        }
        return mapping[self.status]

    def get_conflicting_schedules(self):
        if not self.start_at or not self.duration_hours:
            return Schedule.objects.none()

        lookup = Schedule.objects.exclude(pk=self.pk).exclude(status=self.Status.CANCELED)
        filters = Q()
        if self.owner_id:
            filters |= Q(owner_id=self.owner_id)
        if self.student_id:
            filters |= Q(student_id=self.student_id)
        if not filters:
            return Schedule.objects.none()

        lower_bound = self.start_at - timedelta(days=1)
        upper_bound = self.end_at + timedelta(days=1)
        candidates = lookup.filter(filters, start_at__gte=lower_bound, start_at__lte=upper_bound)
        conflicts = []
        for other in candidates:
            if self.start_at < other.end_at and other.start_at < self.end_at:
                conflicts.append(other.pk)
        return Schedule.objects.filter(pk__in=conflicts)

    def clean(self):
        errors = {}
        if self.service_plan_id and self.student_id and self.service_plan.student_id != self.student_id:
            errors["service_plan"] = "服务方案必须属于当前学员。"
        if self.title == "":
            self.title = f"{self.student.name} - {self.service_plan.subject}" if self.student_id and self.service_plan_id else ""
        conflicts = list(self.get_conflicting_schedules())
        if conflicts:
            errors["start_at"] = "当前时间段与同一执行账号或同一学员的现有排课冲突。"
        if errors:
            raise ValidationError(errors)

    def ensure_series_group(self):
        if self.recurrence_rule and not self.recurrence_group:
            self.recurrence_group = uuid.uuid4()

    def save(self, *args, **kwargs):
        self.ensure_series_group()
        super().save(*args, **kwargs)
