from django.core.management.base import BaseCommand

from reminders.services import scan_course_reminders, scan_receivable_reminders


class Command(BaseCommand):
    help = "统一扫描课程提醒和待收款提醒。"

    def handle(self, *args, **options):
        created_courses = scan_course_reminders()
        created_receivables = scan_receivable_reminders()
        self.stdout.write(
            self.style.SUCCESS(
                f"提醒扫描完成，课程提醒 {created_courses} 条，待收款提醒 {created_receivables} 条。"
            )
        )
