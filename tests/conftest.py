from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from students.models import ServicePlan, Student


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="tester",
        password="ChangeMe123!",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def student(user):
    return Student.objects.create(
        name="测试学员",
        nickname="小测",
        phone="13800000001",
        parent_phone="13900000001",
        status=Student.Status.ACTIVE,
        service_type="数学家教",
        owner=user,
    )


@pytest.fixture
def service_plan(student):
    return ServicePlan.objects.create(
        student=student,
        subject="数学",
        settlement_mode=ServicePlan.SettlementMode.PACKAGE,
        unit_price=Decimal("300.00"),
        total_hours=Decimal("10.00"),
        remaining_hours=Decimal("10.00"),
        owed_hours=Decimal("0.00"),
        effective_from=timezone.localdate(),
        is_active=True,
    )
