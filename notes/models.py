from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from students.models import TimeStampedModel


class SessionNote(TimeStampedModel):
    student = models.ForeignKey(
        "students.Student",
        verbose_name="学员",
        related_name="notes",
        on_delete=models.CASCADE,
    )
    schedule = models.ForeignKey(
        "schedules.Schedule",
        verbose_name="排课",
        related_name="notes",
        on_delete=models.CASCADE,
    )
    completion = models.ForeignKey(
        "lesson_sessions.LessonSession",
        verbose_name="完成记录",
        related_name="notes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    summary = models.TextField("课后情况")
    next_focus = models.TextField("下次重点", blank=True)
    internal_note = models.TextField("内部备注", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="记录人",
        related_name="session_notes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "课后备注"
        verbose_name_plural = "课后备注"

    def clean(self):
        errors = {}
        if self.schedule_id and self.student_id and self.schedule.student_id != self.student_id:
            errors["student"] = "备注学员必须与排课学员一致。"
        if self.completion_id and self.completion.schedule_id != self.schedule_id:
            errors["completion"] = "完成记录必须属于当前排课。"
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.student.name} - 备注"
