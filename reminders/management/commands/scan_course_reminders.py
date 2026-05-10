from django.core.management.base import BaseCommand

from reminders.services import scan_course_reminders


class Command(BaseCommand):
    help = "扫描即将开始的课程并生成提醒任务。"

    def handle(self, *args, **options):
        created = scan_course_reminders()
        self.stdout.write(self.style.SUCCESS(f"课程提醒扫描完成，新增 {created} 条。"))
