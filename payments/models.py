from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum

from students.models import TimeStampedModel, ZERO_DECIMAL


class Receivable(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "待收"
        PARTIAL = "partial", "部分收款"
        PAID = "paid", "已收"

    student = models.ForeignKey(
        "students.Student",
        verbose_name="学员",
        related_name="receivables",
        on_delete=models.CASCADE,
    )
    service_plan = models.ForeignKey(
        "students.ServicePlan",
        verbose_name="服务方案",
        related_name="receivables",
        on_delete=models.PROTECT,
    )
    title = models.CharField("标题", max_length=128)
    amount_due = models.DecimalField(
        "应收金额",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(ZERO_DECIMAL)],
    )
    amount_received = models.DecimalField(
        "实收汇总",
        max_digits=10,
        decimal_places=2,
        default=ZERO_DECIMAL,
        validators=[MinValueValidator(ZERO_DECIMAL)],
    )
    issue_date = models.DateField("应收日期")
    due_date = models.DateField("到期日期")
    status = models.CharField("状态", max_length=16, choices=Status.choices, default=Status.PENDING)
    note = models.TextField("备注", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="创建人",
        related_name="created_receivables",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["status", "due_date", "id"]
        verbose_name = "应收记录"
        verbose_name_plural = "应收记录"
        indexes = [
            models.Index(fields=["status", "due_date"], name="receivable_status_due_idx"),
            models.Index(fields=["student", "due_date"], name="receivable_student_due_idx"),
        ]

    def clean(self):
        errors = {}
        if self.service_plan_id and self.student_id and self.service_plan.student_id != self.student_id:
            errors["service_plan"] = "服务方案必须属于当前学员。"
        if self.due_date < self.issue_date:
            errors["due_date"] = "到期日期不能早于应收日期。"
        if errors:
            raise ValidationError(errors)

    def refresh_summary(self, commit: bool = True):
        total = self.entries.aggregate(total=Sum("amount")).get("total") or ZERO_DECIMAL
        self.amount_received = total
        if total == ZERO_DECIMAL:
            self.status = self.Status.PENDING
        elif total < self.amount_due:
            self.status = self.Status.PARTIAL
        else:
            self.status = self.Status.PAID
        if commit:
            self.save(update_fields=["amount_received", "status", "updated_at"])

    @property
    def outstanding_amount(self) -> Decimal:
        outstanding = self.amount_due - self.amount_received
        return outstanding if outstanding > ZERO_DECIMAL else ZERO_DECIMAL

    def __str__(self) -> str:
        return f"{self.student.name} - {self.title}"


class PaymentEntry(TimeStampedModel):
    class Method(models.TextChoices):
        BANK = "bank", "银行转账"
        WECHAT = "wechat", "微信"
        ALIPAY = "alipay", "支付宝"
        CASH = "cash", "现金"
        OTHER = "other", "其他"

    receivable = models.ForeignKey(
        Receivable,
        verbose_name="应收记录",
        related_name="entries",
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(
        "收款金额",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    method = models.CharField("收款方式", max_length=16, choices=Method.choices, default=Method.BANK)
    received_at = models.DateTimeField("收款时间")
    note = models.TextField("备注", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="记录人",
        related_name="payment_entries",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-received_at", "-id"]
        verbose_name = "实收流水"
        verbose_name_plural = "实收流水"
        indexes = [
            models.Index(fields=["received_at"], name="payment_entry_received_idx"),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.receivable.refresh_summary(commit=True)

    def delete(self, *args, **kwargs):
        receivable = self.receivable
        super().delete(*args, **kwargs)
        receivable.refresh_summary(commit=True)

    def __str__(self) -> str:
        return f"{self.receivable.student.name} - {self.amount}"
