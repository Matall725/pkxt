from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from payments.models import PaymentEntry, Receivable
from reminders.models import ReminderTask
from reminders.services import scan_course_reminders, scan_receivable_reminders
from schedules.forms import ScheduleForm
from schedules.models import Schedule
from schedules.services import create_schedule_batch
from sessions.services import upsert_completion
from students.models import Student


@pytest.mark.django_db
def test_login_required_pages_redirect_anonymous(client):
    for url in ["/", "/students/", "/schedules/", "/payments/", "/reminders/", "/reports/"]:
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_dashboard_home_contains_shortcut_entries(client, user):
    client.force_login(user)
    response = client.get(reverse("dashboard:home"))
    content = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "新增学员" in content
    assert "快速排课" in content
    assert "登记应收" in content
    assert "扫描提醒" in content


@pytest.mark.django_db
@override_settings(ONE_CLICK_LOGIN_ENABLED=True)
def test_login_page_shows_one_click_entry(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200
    assert "本地一键登录" in response.content.decode("utf-8")


@pytest.mark.django_db
@override_settings(ONE_CLICK_LOGIN_ENABLED=True, ONE_CLICK_LOGIN_USERNAME="owner")
def test_one_click_login_creates_or_logs_in_owner(client):
    User = get_user_model()
    assert not User.objects.filter(username="owner").exists()
    response = client.post(reverse("quick-login"), {"next": reverse("dashboard:home")})
    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard:home")
    assert User.objects.filter(username="owner").exists()
    assert client.session.get("_auth_user_id") == str(User.objects.get(username="owner").pk)


@pytest.mark.django_db
def test_csrf_failure_uses_friendly_page():
    csrf_client = pytest.importorskip("django.test").Client(enforce_csrf_checks=True)
    response = csrf_client.post(
        reverse("login"),
        {
            "username": "nobody",
            "password": "bad-password",
            "csrfmiddlewaretoken": "bad-token",
        },
    )
    assert response.status_code == 403
    content = response.content.decode("utf-8")
    assert "表单已经过期或页面不是最新状态" in content
    assert "重新登录" in content


@pytest.mark.django_db
def test_schedule_conflict_validation_blocks_overlap(user, student, service_plan):
    local_tomorrow = timezone.localtime(timezone.now() + timezone.timedelta(days=1))
    start_at = local_tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    Schedule.objects.create(
        student=student,
        service_plan=service_plan,
        owner=user,
        title="已有课程",
        start_at=start_at,
        duration_hours=Decimal("1.00"),
        status=Schedule.Status.PENDING,
        delivery_mode=Schedule.DeliveryMode.ONLINE,
    )
    conflict = Schedule(
        student=student,
        service_plan=service_plan,
        owner=user,
        title="冲突课程",
        start_at=start_at + timezone.timedelta(minutes=30),
        duration_hours=Decimal("1.00"),
        status=Schedule.Status.PENDING,
        delivery_mode=Schedule.DeliveryMode.ONLINE,
    )
    with pytest.raises(ValidationError):
        conflict.full_clean()


@pytest.mark.django_db
def test_series_schedule_creation_generates_multiple_records(user, student, service_plan):
    local_tomorrow = timezone.localtime(timezone.now() + timezone.timedelta(days=1))
    start_at = local_tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    schedules = create_schedule_batch(
        owner=user,
        cleaned_data={
            "student": student,
            "service_plan": service_plan,
            "title": "系列课程",
            "start_at": start_at,
            "duration_hours": Decimal("1.00"),
            "status": Schedule.Status.PENDING,
            "delivery_mode": Schedule.DeliveryMode.ONLINE,
            "location": "腾讯会议",
            "repeat_frequency": ScheduleForm.RepeatFrequency.WEEKLY,
            "repeat_interval": 1,
            "repeat_count": 3,
            "update_scope": ScheduleForm.Scope.SINGLE,
        },
    )
    assert len(schedules) == 3
    assert schedules[0].recurrence_group is not None
    assert schedules[1].recurrence_group == schedules[0].recurrence_group


@pytest.mark.django_db
def test_completion_deducts_hours_and_records_owed(user, student, service_plan):
    service_plan.remaining_hours = Decimal("1.00")
    service_plan.save(update_fields=["remaining_hours"])
    local_tomorrow = timezone.localtime(timezone.now() + timezone.timedelta(days=1))
    start_at = local_tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    schedule = Schedule.objects.create(
        student=student,
        service_plan=service_plan,
        owner=user,
        title="待完成课程",
        start_at=start_at,
        duration_hours=Decimal("1.50"),
        status=Schedule.Status.PENDING,
        delivery_mode=Schedule.DeliveryMode.ONLINE,
    )
    completion = upsert_completion(
        schedule=schedule,
        attendance_status="present",
        actual_duration_hours=Decimal("1.50"),
        operator=user,
    )
    service_plan.refresh_from_db()
    schedule.refresh_from_db()
    assert schedule.status == Schedule.Status.COMPLETED
    assert completion.deducted_hours == Decimal("1.50")
    assert service_plan.remaining_hours == Decimal("0.00")
    assert service_plan.owed_hours == Decimal("0.50")


@pytest.mark.django_db
def test_receivable_status_updates_from_multiple_entries(user, student, service_plan):
    receivable = Receivable.objects.create(
        student=student,
        service_plan=service_plan,
        title="测试应收",
        amount_due=Decimal("1200.00"),
        issue_date=timezone.localdate(),
        due_date=timezone.localdate(),
        created_by=user,
    )
    PaymentEntry.objects.create(
        receivable=receivable,
        amount=Decimal("500.00"),
        method=PaymentEntry.Method.WECHAT,
        received_at=timezone.now(),
        created_by=user,
    )
    receivable.refresh_from_db()
    assert receivable.status == Receivable.Status.PARTIAL
    PaymentEntry.objects.create(
        receivable=receivable,
        amount=Decimal("700.00"),
        method=PaymentEntry.Method.BANK,
        received_at=timezone.now(),
        created_by=user,
    )
    receivable.refresh_from_db()
    assert receivable.status == Receivable.Status.PAID
    assert receivable.amount_received == Decimal("1200.00")


@pytest.mark.django_db
def test_reminder_scans_create_course_and_receivable_tasks(user, student, service_plan):
    mock_now = timezone.make_aware(timezone.datetime(2026, 5, 27, 14, 0, 0), timezone.get_current_timezone())
    with patch("django.utils.timezone.now", return_value=mock_now):
        Schedule.objects.create(
            student=student,
            service_plan=service_plan,
            owner=user,
            title="临近课程",
            start_at=mock_now + timezone.timedelta(minutes=30),
            duration_hours=Decimal("0.50"),
            status=Schedule.Status.PENDING,
            delivery_mode=Schedule.DeliveryMode.ONLINE,
        )
        Receivable.objects.create(
            student=student,
            service_plan=service_plan,
            title="测试应收",
            amount_due=Decimal("500.00"),
            issue_date=timezone.localdate(),
            due_date=timezone.localdate(),
            created_by=user,
        )
        assert scan_course_reminders() == 1
        assert scan_receivable_reminders() == 1
        assert set(ReminderTask.objects.values_list("reminder_type", flat=True)) == {"course", "receivable"}


@pytest.mark.django_db
def test_report_exports_return_downloads(client, user, student, service_plan):
    receivable = Receivable.objects.create(
        student=student,
        service_plan=service_plan,
        title="测试应收",
        amount_due=Decimal("500.00"),
        issue_date=timezone.localdate(),
        due_date=timezone.localdate(),
        created_by=user,
    )
    PaymentEntry.objects.create(
        receivable=receivable,
        amount=Decimal("200.00"),
        method=PaymentEntry.Method.WECHAT,
        received_at=timezone.now(),
        created_by=user,
    )
    client.force_login(user)
    assert client.get(reverse("dashboard:export-students")).status_code == 200
    assert client.get(reverse("dashboard:export-receivables")).status_code == 200
    assert client.get(reverse("dashboard:export-hours")).status_code == 200
    assert client.get(reverse("dashboard:export-finance")).status_code == 200


@pytest.mark.django_db
def test_student_management_create_flow(client, user):
    client.force_login(user)
    response = client.post(
        reverse("students:create"),
        data={
            "name": "新学员",
            "nickname": "小新",
            "gender": Student.Gender.UNKNOWN,
            "age": "12",
            "phone": "13800000088",
            "parent_phone": "13900000088",
            "tags": "试听,转介绍",
            "source_channel": "朋友推荐",
            "status": Student.Status.ACTIVE,
            "service_type": "数学家教",
            "risk_flag": "",
            "attention_note": "需要重点跟进基础。",
            "plans-TOTAL_FORMS": "1",
            "plans-INITIAL_FORMS": "0",
            "plans-MIN_NUM_FORMS": "0",
            "plans-MAX_NUM_FORMS": "1000",
            "plans-0-subject": "数学",
            "plans-0-settlement_mode": "package",
            "plans-0-unit_price": "300.00",
            "plans-0-total_hours": "20.00",
            "plans-0-remaining_hours": "20.00",
            "plans-0-owed_hours": "0.00",
            "plans-0-effective_from": timezone.localdate().isoformat(),
            "plans-0-expires_at": "",
            "plans-0-is_active": "on",
        },
    )
    assert response.status_code == 302
    created = Student.objects.get(name="新学员", phone="13800000088")
    assert created.owner == user
    assert created.service_plans.count() == 1
    list_response = client.get(reverse("students:list"))
    assert list_response.status_code == 200
    assert "新学员" in list_response.content.decode("utf-8")


@pytest.mark.django_db
def test_schedule_outside_working_hours_validation(user, student, service_plan):
    local_tomorrow = timezone.localtime(timezone.now() + timezone.timedelta(days=1))

    # 1. Start time too early (e.g., 8:00 AM local time)
    early_start = local_tomorrow.replace(hour=8, minute=0, second=0, microsecond=0)
    schedule_early = Schedule(
        student=student,
        service_plan=service_plan,
        owner=user,
        title="太早的课程",
        start_at=early_start,
        duration_hours=Decimal("1.00"),
        status=Schedule.Status.PENDING,
        delivery_mode=Schedule.DeliveryMode.ONLINE,
    )
    with pytest.raises(ValidationError) as excinfo:
        schedule_early.full_clean()
    assert "排课时间必须在工作时间（9:00 - 21:00）范围内。" in str(excinfo.value)

    # 2. End time too late (e.g., starts at 8:30 PM local time, lasts 1 hour -> ends at 9:30 PM)
    late_start = local_tomorrow.replace(hour=20, minute=30, second=0, microsecond=0)
    schedule_late = Schedule(
        student=student,
        service_plan=service_plan,
        owner=user,
        title="太晚的课程",
        start_at=late_start,
        duration_hours=Decimal("1.00"),
        status=Schedule.Status.PENDING,
        delivery_mode=Schedule.DeliveryMode.ONLINE,
    )
    with pytest.raises(ValidationError) as excinfo:
        schedule_late.full_clean()
    assert "排课时间必须在工作时间（9:00 - 21:00）范围内。" in str(excinfo.value)

    # 3. Spans across days (e.g., starts at 10:00 PM local time, lasts 2 hours -> ends at 12:00 AM next day)
    cross_day_start = local_tomorrow.replace(hour=22, minute=0, second=0, microsecond=0)
    schedule_cross = Schedule(
        student=student,
        service_plan=service_plan,
        owner=user,
        title="跨天课程",
        start_at=cross_day_start,
        duration_hours=Decimal("2.00"),
        status=Schedule.Status.PENDING,
        delivery_mode=Schedule.DeliveryMode.ONLINE,
    )
    with pytest.raises(ValidationError) as excinfo:
        schedule_cross.full_clean()
    assert "排课时间必须在工作时间（9:00 - 21:00）范围内。" in str(excinfo.value)

