import json
from unittest.mock import MagicMock, patch
import pytest
from django.urls import reverse
from django.utils import timezone
from schedules.models import Schedule
from students.models import Student, ServicePlan
from notes.models import SessionNote
from ai_gateway.clients.anthropic_client import RobustAnthropicClient
from ai_gateway.models import AIAuditLog


@pytest.fixture
def mock_anthropic_response():
    """
    模拟 Anthropic Claude 3.5 Sonnet 的响应结构，包含 Prompt Caching 字段。
    """
    response = MagicMock()
    response.content = [
        MagicMock(text="Hello! I am Claude, your AI scheduling assistant.")
    ]
    response.usage = MagicMock()
    response.usage.input_tokens = 1000
    response.usage.output_tokens = 200
    # 模拟缓存命中字段
    response.usage.cache_read_input_tokens = 800
    return response


@pytest.fixture
def mock_feedback_response():
    """
    模拟 AI 课后反馈生成器返回的结构化 JSON 响应。
    """
    feedback_json = json.dumps({
        "skills_covered": ["一元二次方程求根公式", "因式分解"],
        "performance_level": "小明今天上课注意力很集中，公式记忆迅速，但在做题速度上还有提升空间。",
        "struggles_identified": ["十字相乘法不够熟练"],
        "assigned_drills": ["完成课后习题3道", "复习公式"],
        "encouragement": "小明今天表现很棒，继续保持这个势头，你一定能攻克这个难关！"
    })
    response = MagicMock()
    response.content = [
        MagicMock(text=feedback_json)
    ]
    response.usage = MagicMock()
    response.usage.input_tokens = 1200
    response.usage.output_tokens = 300
    response.usage.cache_read_input_tokens = 1000
    return response


@pytest.mark.django_db
def test_ai_audit_log_cost_calculation():
    """
    测试 AIAuditLog 模型在保存时是否能正确计算成本 (USD) 和缓存命中率。
    """
    log1 = AIAuditLog.objects.create(
        feature_name="test_feature",
        raw_prompt="System: Hello\nUser: Hi",
        raw_response="Hello there",
        input_tokens=1000,
        output_tokens=200,
        input_tokens_cached=800,
        latency_ms=500
    )
    assert float(log1.cost_usd) == pytest.approx(0.00384, abs=1e-6)
    assert log1.cache_hit_rate == 0.8

    log2 = AIAuditLog.objects.create(
        feature_name="test_zero",
        raw_prompt="",
        raw_response="",
        input_tokens=0,
        output_tokens=0,
        input_tokens_cached=0,
        latency_ms=100
    )
    assert float(log2.cost_usd) == 0.0
    assert log2.cache_hit_rate == 0.0


@pytest.mark.django_db
@patch("anthropic.resources.beta.messages.Messages.create")
def test_robust_anthropic_client_success(mock_create, mock_anthropic_response):
    """
    测试 RobustAnthropicClient 在 API 调用成功时是否能正常工作并记录审计日志。
    """
    mock_create.return_value = mock_anthropic_response

    client = RobustAnthropicClient(api_key="test-api-key")
    response = client.call_with_prompt_cache(
        feature_name="copilot_test",
        system_prompt="You are a helpful assistant.",
        messages=[{"role": "user", "content": "Hello"}],
        input_params={"q": "Hello"}
    )

    mock_create.assert_called_once()
    assert "Hello! I am Claude" in response.content[0].text

    audit_log = AIAuditLog.objects.get(feature_name="copilot_test")
    assert audit_log.input_tokens == 1000
    assert audit_log.output_tokens == 200
    assert audit_log.input_tokens_cached == 800
    assert float(audit_log.cost_usd) == pytest.approx(0.00384, abs=1e-6)


@pytest.mark.django_db
@patch("anthropic.resources.beta.messages.Messages.create")
def test_robust_anthropic_client_failure(mock_create):
    """
    测试 RobustAnthropicClient 在 API 报错时是否能记录失败的审计日志，并向外抛出异常。
    """
    from anthropic import APIStatusError
    mock_create.side_effect = APIStatusError(
        message="Rate limit exceeded",
        response=MagicMock(status_code=429),
        body={}
    )

    client = RobustAnthropicClient(api_key="test-api-key")

    with pytest.raises(APIStatusError):
        client.call_with_prompt_cache(
            feature_name="copilot_fail",
            system_prompt="System",
            messages=[{"role": "user", "content": "Hi"}]
        )

    audit_log = AIAuditLog.objects.filter(feature_name="copilot_fail").last()
    assert "Error: Rate limit exceeded" in audit_log.raw_response
    assert audit_log.input_tokens == 0
    assert audit_log.output_tokens == 0


@pytest.mark.django_db
@patch("anthropic.resources.beta.messages.Messages.create")
def test_generate_feedback_api(mock_create, mock_feedback_response, client, user, student, service_plan):
    """
    测试 AI 课后反馈生成接口的完整业务流程。
    """
    # 模拟登录
    client.force_login(user)
    mock_create.return_value = mock_feedback_response

    # 创建一个排课记录
    local_tomorrow = timezone.localtime(timezone.now() + timezone.timedelta(days=1))
    start_at = local_tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    schedule = Schedule.objects.create(
        student=student,
        service_plan=service_plan,
        owner=user,
        title="数学课",
        start_at=start_at,
        duration_hours=2.0,
        status=Schedule.Status.COMPLETED
    )

    # 调用生成反馈的 API
    url = reverse("ai_gateway:generate_feedback")
    response = client.post(url, {
        "schedule_id": schedule.id,
        "draft_text": "今天讲了求根公式，公式记住了，做题有点慢，留了3道题",
        "tone": "encouraging"
    })

    assert response.status_code == 200
    data = response.json()

    # 验证返回的结构化数据是否与 Mock 一致
    assert data["skills_covered"] == ["一元二次方程求根公式", "因式分解"]
    assert "小明今天上课注意力很集中" in data["performance_level"]
    assert data["struggles_identified"] == ["十字相乘法不够熟练"]
    assert data["assigned_drills"] == ["完成课后习题3道", "复习公式"]
    assert "小明今天表现很棒" in data["encouragement"]

    # 验证审计日志是否成功记录
    audit_log = AIAuditLog.objects.get(feature_name="generate_feedback")
    assert audit_log.input_tokens == 1200
    assert audit_log.output_tokens == 300
    assert audit_log.input_tokens_cached == 1000
    assert audit_log.input_parameters["schedule_id"] == str(schedule.id)


@pytest.mark.django_db
def test_lookup_student_tool(student):
    """
    测试 lookup_student 工具是否能正确模糊查询学员。
    """
    from ai_gateway.agents.scheduler_agent import lookup_student
    results = lookup_student(student.name[:2])
    assert len(results) >= 1
    assert results[0]["id"] == student.id
    assert results[0]["name"] == student.name


@pytest.mark.django_db
def test_verify_schedule_conflicts_tool(student, user, service_plan):
    """
    测试 verify_schedule_conflicts 工具是否能正确检测冲突。
    """
    from ai_gateway.agents.scheduler_agent import verify_schedule_conflicts
    # 构造一个无冲突的时间
    start_at = "2026-06-03T15:00:00"
    res = verify_schedule_conflicts(student_id=student.id, start_at=start_at, duration_hours=2.0, owner_id=user.id)
    assert res["has_conflict"] is False
    assert res["outside_working_hours"] is False

    # 构造一个在工作时间外的排课
    start_at_early = "2026-06-03T08:00:00"
    res_early = verify_schedule_conflicts(student_id=student.id, start_at=start_at_early, duration_hours=2.0, owner_id=user.id)
    assert res_early["outside_working_hours"] is True

    # 创建一个排课记录以制造冲突
    from schedules.models import Schedule
    from django.utils.dateparse import parse_datetime
    dt = parse_datetime(start_at)
    dt = timezone.make_aware(dt, timezone.get_current_timezone())

    Schedule.objects.create(
        student=student,
        service_plan=service_plan,
        owner=user,
        title="冲突课",
        start_at=dt,
        duration_hours=2.0,
        status=Schedule.Status.PENDING
    )

    res2 = verify_schedule_conflicts(student_id=student.id, start_at=start_at, duration_hours=2.0, owner_id=user.id)
    assert res2["has_conflict"] is True
    assert len(res2["conflicts"]) == 1


@pytest.mark.django_db
def test_approve_proposal_api(client, user, student, service_plan):
    """
    测试确认排课建议接口。
    """
    client.force_login(user)
    url = reverse("ai_gateway:approve_proposal")
    response = client.post(url, {
        "student_id": student.id,
        "service_plan_id": service_plan.id,
        "start_at": "2026-06-03T15:00:00",
        "duration_hours": "2.0"
    })
    assert response.status_code == 200
    assert "排课成功" in response.content.decode("utf-8")
    assert Schedule.objects.filter(student=student, service_plan=service_plan).exists()


@pytest.mark.django_db
def test_reject_proposal_api(client, user):
    """
    测试拒绝排课建议接口。
    """
    client.force_login(user)
    url = reverse("ai_gateway:reject_proposal")
    response = client.post(url)
    assert response.status_code == 200
    assert "已取消" in response.content.decode("utf-8")


@pytest.mark.django_db
@patch("anthropic.resources.beta.messages.Messages.create")
def test_student_portrait_api(mock_create, client, user, student, service_plan):
    """
    测试生成学员画像接口。
    """
    client.force_login(user)

    # 模拟 Anthropic 响应
    response_mock = MagicMock()
    response_mock.content = [
        MagicMock(text="<div class='student-portrait'>学习特点与习惯：小明很聪明...</div>")
    ]
    response_mock.usage = MagicMock()
    response_mock.usage.input_tokens = 1000
    response_mock.usage.output_tokens = 200
    response_mock.usage.cache_read_input_tokens = 800
    mock_create.return_value = response_mock

    # 创建一个排课记录和课后备注
    local_tomorrow = timezone.localtime(timezone.now() + timezone.timedelta(days=1))
    start_at = local_tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    schedule = Schedule.objects.create(
        student=student,
        service_plan=service_plan,
        owner=user,
        title="数学课",
        start_at=start_at,
        duration_hours=2.0,
        status=Schedule.Status.COMPLETED
    )

    SessionNote.objects.create(
        student=student,
        schedule=schedule,
        summary="今天讲了求根公式，掌握得很好",
        next_focus="复习因式分解",
        created_by=user
    )

    url = reverse("ai_gateway:student_portrait")
    response = client.get(f"{url}?student_id={student.id}")
    assert response.status_code == 200
    assert "student-portrait" in response.content.decode("utf-8")

