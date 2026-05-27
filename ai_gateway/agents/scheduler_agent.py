import json
from datetime import datetime, time
from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from students.models import Student, ServicePlan
from schedules.models import Schedule
from payments.models import Receivable

def lookup_student(name: str):
    """
    根据姓名或昵称模糊查询学员信息，返回学员ID、姓名、状态、标签等。
    """
    students = Student.objects.filter(
        Q(name__icontains=name) | Q(nickname__icontains=name)
    )
    results = []
    for s in students:
        results.append({
            "id": s.id,
            "name": s.name,
            "nickname": s.nickname,
            "status": s.status,
            "tags": s.tags,
            "attention_note": s.attention_note
        })
    return results

def get_student_service_plans(student_id: int):
    """
    根据学员ID获取该学员的所有服务方案（包括科目、结算模式、剩余课时、是否生效等）。
    """
    plans = ServicePlan.objects.filter(student_id=student_id)
    results = []
    for p in plans:
        results.append({
            "id": p.id,
            "subject": p.subject,
            "settlement_mode": p.settlement_mode,
            "remaining_hours": str(p.remaining_hours) if p.remaining_hours is not None else None,
            "is_active": p.is_active
        })
    return results

def verify_schedule_conflicts(student_id: int, start_at: str, duration_hours: float, owner_id: int = None):
    """
    验证拟排课时间段是否与该学员或老师的现有排课冲突，并检查是否在工作时间（9:00 - 21:00）内。
    """
    dt = parse_datetime(start_at)
    if not dt:
        return {"error": f"Invalid datetime format: {start_at}"}

    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())

    local_start = timezone.localtime(dt)
    local_end = local_start + timezone.timedelta(minutes=int(Decimal(str(duration_hours)) * Decimal("60")))

    outside_working_hours = (
        local_start.time() < time(9, 0)
        or local_end.time() > time(21, 0)
        or local_start.date() != local_end.date()
    )

    temp_schedule = Schedule(
        student_id=student_id,
        start_at=dt,
        duration_hours=Decimal(str(duration_hours)),
        owner_id=owner_id
    )

    conflicts = temp_schedule.get_conflicting_schedules()
    results = []
    for c in conflicts:
        results.append({
            "id": c.id,
            "title": c.title,
            "start_at": timezone.localtime(c.start_at).isoformat(),
            "duration_hours": str(c.duration_hours),
            "owner_name": c.owner.username if c.owner else None
        })
    return {
        "outside_working_hours": outside_working_hours,
        "has_conflict": len(results) > 0,
        "conflicts": results
    }

def get_receivable_payment_history(receivable_id: int):
    """
    根据应收记录ID获取该应收记录的详细信息以及该学员的历史收款记录，用于分析缴费习惯并起草催款话术。
    """
    try:
        receivable = Receivable.objects.select_related("student", "service_plan").get(pk=receivable_id)
    except Receivable.DoesNotExist:
        return {"error": f"Receivable record {receivable_id} does not exist."}

    student_receivables = Receivable.objects.filter(student=receivable.student).order_by("due_date")
    history = []
    for r in student_receivables:
        history.append({
            "id": r.id,
            "title": r.title,
            "amount_due": str(r.amount_due),
            "amount_received": str(r.amount_received),
            "status": r.status,
            "due_date": r.due_date.isoformat(),
            "issue_date": r.issue_date.isoformat(),
        })

    return {
        "student_name": receivable.student.name,
        "receivable_title": receivable.title,
        "amount_due": str(receivable.amount_due),
        "outstanding_amount": str(receivable.outstanding_amount),
        "due_date": receivable.due_date.isoformat(),
        "payment_history": history
    }

def get_scheduler_system_prompt() -> str:
    return """你是一个专业的排课与收款助手（AI Copilot Agent）。
今天是 2026年5月26日，星期二。

你的任务是协助老师进行排课或起草催款话术。

【排课流程】
当用户提出排课请求时，请按以下步骤执行：
1. 使用 `lookup_student` 工具查询学员。如果找到多个匹配的学员，请列出并让用户确认；如果未找到，请告知用户。
2. 确定学员后，使用 `get_student_service_plans` 获取该学员的服务方案。
   - 如果学员没有生效中的服务方案，告知用户无法排课。
   - 如果有多个方案，请询问用户使用哪一个。
3. 根据用户描述的时间（如“明天下午3点”、“下周三”），结合今天日期（2026-05-26，星期二）计算出具体的 ISO 时间字符串（例如“2026-05-27T15:00:00”）。
   - 注意：排课的本地时间必须在工作时间（9:00 - 21:00）范围内，即开始时间不早于 9:00，结束时间不晚于 21:00。如果用户提供的时间不在此范围内，请直接提示用户并建议其调整时间。
4. 使用 `verify_schedule_conflicts` 验证该时间段是否存在冲突以及是否在工作时间内。
   - 如果时间段不在工作时间（9:00 - 21:00）内（即 `outside_working_hours` 为 true），告知用户排课时间必须在工作时间内，并建议用户调整时间。
   - 如果存在冲突，列出冲突的排课信息，并建议用户调整时间。
   - 如果没有冲突且在工作时间内，且所有信息完整（学员、服务方案、开始时间、时长），请输出排课确认卡片。

【排课确认卡片输出格式要求】
当你确认可以排课时，除了文字回复外，你必须在回复的末尾输出一个 HTML 格式的排课确认卡片。
为了防止前端 Markdown 解析器在换行时插入 <br> 破坏 HTML 结构，请将整个 HTML 卡片写在单行中，不要有换行符。
HTML 卡片模板如下（请用实际数据替换大括号中的变量）：
<div class="ai-proposal-card mt-2 p-3 border rounded bg-light"><h6 class="text-primary mb-2"><i class="bi bi-calendar-plus"></i> 确认排课建议</h6><div class="small mb-3"><strong>学员：</strong>{student_name}<br><strong>服务方案：</strong>{plan_subject} ({settlement_mode_display})<br><strong>时间：</strong>{start_at_display}<br><strong>时长：</strong>{duration_hours} 小时<br></div><div class="d-flex gap-2"><button class="btn btn-sm btn-primary" hx-post="/ai/copilot/approve-proposal/" hx-vals='{{"student_id": {student_id}, "service_plan_id": {service_plan_id}, "start_at": "{start_at_iso}", "duration_hours": {duration_hours}}}' hx-target="closest .ai-proposal-card" hx-swap="outerHTML">确认排课</button><button class="btn btn-sm btn-outline-secondary" hx-post="/ai/copilot/reject-proposal/" hx-target="closest .ai-proposal-card" hx-swap="outerHTML">拒绝</button></div></div>

【催款话术生成流程】
当用户提出催款话术生成请求，或提供应收记录ID时：
1. 使用 `get_receivable_payment_history` 工具获取该应收记录的详细信息及历史收款记录。
2. 分析该学员的历史缴费习惯（如是否有逾期记录、是否每次都按时支付等）。
3. 起草一份有温度、专业且得体稳妥的催款话术，话术中应包含：
   - 学员姓名
   - 欠款金额
   - 账单到期日期
   - 友好的付款提示和支付方式引导。
4. 话术应根据历史缴费习惯调整语气（例如：对于一贯准时但偶尔忘记的家长，语气应极其温和、提醒为主；对于经常拖欠的家长，语气应坚定且明确截止时间）。

注意：
- 结算模式显示名称：课包制请显示“课包制”，按次结算请显示“按次结算”。
- 务必保证 hx-vals 中的 JSON 格式正确，属性名和属性值使用双引号，整个 hx-vals 用单引号包裹。
- 不要输出任何 ```html 等 Markdown 代码块包裹 HTML 卡片，直接输出 HTML 字符串即可。
"""

SCHEDULER_TOOLS = [
    {
        "name": "lookup_student",
        "description": "根据姓名或昵称模糊查询学员信息，返回学员ID、姓名、状态、标签等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "学员姓名或昵称"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "get_student_service_plans",
        "description": "根据学员ID获取该学员的所有服务方案（包括科目、结算模式、剩余课时、是否生效等）。",
        "input_schema": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "integer",
                    "description": "学员ID"
                }
            },
            "required": ["student_id"]
        }
    },
    {
        "name": "verify_schedule_conflicts",
        "description": "验证拟排课时间段是否与该学员或老师的现有排课冲突，并检查是否在工作时间（9:00 - 21:00）内。",
        "input_schema": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "integer",
                    "description": "学员ID"
                },
                "start_at": {
                    "type": "string",
                    "description": "拟排课开始时间，ISO格式字符串，如 '2026-05-27T15:00:00'"
                },
                "duration_hours": {
                    "type": "number",
                    "description": "拟排课时长（小时）"
                }
            },
            "required": ["student_id", "start_at", "duration_hours"]
        }
    },
    {
        "name": "get_receivable_payment_history",
        "description": "根据应收记录ID获取该应收记录的详细信息以及该学员的历史收款记录，用于分析缴费习惯并起草催款话术。",
        "input_schema": {
            "type": "object",
            "properties": {
                "receivable_id": {
                    "type": "integer",
                    "description": "应收记录ID"
                }
            },
            "required": ["receivable_id"]
        }
    }
]
