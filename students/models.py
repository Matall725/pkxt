from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


ZERO_DECIMAL = Decimal("0")


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Student(TimeStampedModel):
    class Gender(models.TextChoices):
        UNKNOWN = "unknown", "未说明"
        MALE = "male", "男"
        FEMALE = "female", "女"

    class Status(models.TextChoices):
        LEAD = "lead", "潜在"
        ACTIVE = "active", "服务中"
        PAUSED = "paused", "暂停"
        CLOSED = "closed", "结束"

    name = models.CharField("姓名", max_length=64)
    nickname = models.CharField("昵称", max_length=64, blank=True)
    gender = models.CharField("性别", max_length=16, choices=Gender.choices, default=Gender.UNKNOWN)
    age = models.PositiveSmallIntegerField("年龄", null=True, blank=True)
    phone = models.CharField("手机号", max_length=32)
    parent_phone = models.CharField("家长联系方式", max_length=32, blank=True)
    tags = models.CharField("标签", max_length=255, blank=True, help_text="使用逗号分隔多个标签")
    source_channel = models.CharField("来源渠道", max_length=64, blank=True)
    status = models.CharField("状态", max_length=16, choices=Status.choices, default=Status.ACTIVE)
    service_type = models.CharField("服务类型", max_length=64, blank=True)
    risk_flag = models.CharField("风险标记", max_length=64, blank=True)
    attention_note = models.TextField("重点关注", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="执行账号",
        related_name="students",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "学员"
        verbose_name_plural = "学员"
        constraints = [
            models.UniqueConstraint(fields=["name", "phone"], name="uniq_student_name_phone"),
        ]
        indexes = [
            models.Index(fields=["status"], name="student_status_idx"),
            models.Index(fields=["name"], name="student_name_idx"),
            models.Index(fields=["phone"], name="student_phone_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name}（{self.phone}）"

    @property
    def active_service_plan(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("service_plans")
        if prefetched is not None:
            for plan in prefetched:
                if plan.is_active:
                    return plan
            return None
        return self.service_plans.filter(is_active=True).order_by("-effective_from", "-id").first()


class ServicePlan(TimeStampedModel):
    class SettlementMode(models.TextChoices):
        PACKAGE = "package", "课包制"
        PER_SESSION = "per_session", "按次结算"

    student = models.ForeignKey(
        Student,
        verbose_name="学员",
        related_name="service_plans",
        on_delete=models.CASCADE,
    )
    subject = models.CharField("科目/咨询类型", max_length=128)
    settlement_mode = models.CharField("结算模式", max_length=32, choices=SettlementMode.choices)
    unit_price = models.DecimalField(
        "单价",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(ZERO_DECIMAL)],
    )
    total_hours = models.DecimalField(
        "总课时",
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(ZERO_DECIMAL)],
    )
    remaining_hours = models.DecimalField(
        "剩余课时",
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(ZERO_DECIMAL)],
    )
    owed_hours = models.DecimalField(
        "欠课时",
        max_digits=8,
        decimal_places=2,
        default=ZERO_DECIMAL,
        validators=[MinValueValidator(ZERO_DECIMAL)],
    )
    effective_from = models.DateField("生效日期")
    expires_at = models.DateField("失效日期", null=True, blank=True)
    is_active = models.BooleanField("当前生效", default=True)

    class Meta:
        ordering = ["-is_active", "-effective_from", "-id"]
        verbose_name = "服务方案"
        verbose_name_plural = "服务方案"
        constraints = [
            models.UniqueConstraint(
                fields=["student"],
                condition=Q(is_active=True),
                name="uniq_active_plan_per_student",
            ),
        ]
        indexes = [
            models.Index(fields=["student", "is_active"], name="plan_student_active_idx"),
            models.Index(fields=["settlement_mode"], name="plan_settlement_idx"),
        ]

    def clean(self):
        errors = {}
        if self.settlement_mode == self.SettlementMode.PACKAGE:
            if self.total_hours is None:
                errors["total_hours"] = "课包制必须填写总课时。"
            if self.remaining_hours is None:
                errors["remaining_hours"] = "课包制必须填写剩余课时。"
        else:
            self.total_hours = None
            self.remaining_hours = None

        if self.expires_at and self.expires_at < self.effective_from:
            errors["expires_at"] = "失效日期不能早于生效日期。"

        if self.is_active and self.student_id:
            queryset = ServicePlan.objects.filter(student_id=self.student_id, is_active=True)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            if queryset.exists():
                errors["is_active"] = "同一学员只能有一个生效中的服务方案。"

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.student.name} - {self.subject} - {self.get_settlement_mode_display()}"
