from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from students.models import TimeStampedModel


class ReminderConfig(TimeStampedModel):
    course_enabled = models.BooleanField("启用课程提醒", default=True)
    course_lead_minutes = models.PositiveIntegerField("课程提前提醒分钟", default=60)
    receivable_enabled = models.BooleanField("启用待收款提醒", default=True)
    receivable_due_offset_days = models.PositiveIntegerField("到期偏移天数", default=0)

    class Meta:
        verbose_name = "提醒配置"
        verbose_name_plural = "提醒配置"

    def __str__(self) -> str:
        return "提醒配置"

    @classmethod
    def load(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class ReminderTask(TimeStampedModel):
    class ReminderType(models.TextChoices):
        COURSE = "course", "课程提醒"
        RECEIVABLE = "receivable", "待收款提醒"

    class Status(models.TextChoices):
        PENDING = "pending", "未完成"
        DONE = "done", "已完成"

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    related_object = GenericForeignKey("content_type", "object_id")

    reminder_type = models.CharField("提醒类型", max_length=16, choices=ReminderType.choices)
    remind_at = models.DateTimeField("提醒时间")
    status = models.CharField("执行状态", max_length=16, choices=Status.choices, default=Status.PENDING)
    title = models.CharField("标题", max_length=255)
    message = models.TextField("提醒内容")
    window_key = models.CharField("去重键", max_length=255, unique=True)
    completed_at = models.DateTimeField("完成时间", null=True, blank=True)

    class Meta:
        ordering = ["status", "remind_at", "id"]
        verbose_name = "提醒任务"
        verbose_name_plural = "提醒任务"
        indexes = [
            models.Index(fields=["status", "remind_at"], name="reminder_status_time_idx"),
        ]

    def __str__(self) -> str:
        return self.title
