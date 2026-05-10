from django.core.management.base import BaseCommand

from reminders.services import scan_receivable_reminders


class Command(BaseCommand):
    help = "扫描待收或部分收款记录并生成提醒任务。"

    def handle(self, *args, **options):
        created = scan_receivable_reminders()
        self.stdout.write(self.style.SUCCESS(f"待收款提醒扫描完成，新增 {created} 条。"))
