import json
import time
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from schedules.models import Schedule
from students.models import Student, ServicePlan
from notes.models import SessionNote
from .clients.anthropic_client import RobustAnthropicClient
from .agents.feedback_agent import get_feedback_system_prompt, get_feedback_user_message
from .agents.scheduler_agent import (
    get_scheduler_system_prompt,
    SCHEDULER_TOOLS,
    lookup_student,
    get_student_service_plans,
    verify_schedule_conflicts,
    get_receivable_payment_history
)


@login_required
def stream_copilot_response(request):
    """
    SSE 流式响应接口，处理 AI 智能助理的排课与催款逻辑。
    """
    query = request.GET.get("q", "").strip()
    if not query:
        return HttpResponse("Missing query", status=400)

    def event_stream():
        client = RobustAnthropicClient()
        if not client.client:
            yield f"data: {json.dumps({'text': 'AI 客户端未配置，请检查 API Key。'})}\n\n"
            return

        system_prompt = get_scheduler_system_prompt()
        messages = [{"role": "user", "content": query}]

        max_turns = 5
        for turn in range(max_turns):
            try:
                response = client.call_with_prompt_cache(
                    feature_name="scheduler_copilot",
                    system_prompt=system_prompt,
                    messages=messages,
                    tools=SCHEDULER_TOOLS,
                    input_params={"query_length": len(query), "turn": turn}
                )
            except Exception as e:
                yield f"data: {json.dumps({'text': f'AI 调用失败: {str(e)}'})}\n\n"
                return

            # 检查是否有工具调用
            tool_calls = [content for content in response.content if content.type == "tool_use"]

            if tool_calls:
                # 将 Assistant 的工具使用消息加入上下文
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                tool_results = []
                for tool_call in tool_calls:
                    tool_name = tool_call.name
                    tool_input = tool_call.input
                    tool_id = tool_call.id

                    # 提示前端正在执行工具
                    yield f"data: {json.dumps({'text': f'*(正在执行：{tool_name}...)*\\n'})}\n\n"

                    # 执行具体工具
                    if tool_name == "lookup_student":
                        result = lookup_student(tool_input.get("name", ""))
                    elif tool_name == "get_student_service_plans":
                        result = get_student_service_plans(tool_input.get("student_id"))
                    elif tool_name == "verify_schedule_conflicts":
                        result = verify_schedule_conflicts(
                            student_id=tool_input.get("student_id"),
                            start_at=tool_input.get("start_at"),
                            duration_hours=tool_input.get("duration_hours"),
                            owner_id=request.user.id
                        )
                    elif tool_name == "get_receivable_payment_history":
                        result = get_receivable_payment_history(tool_input.get("receivable_id"))
                    else:
                        result = {"error": f"Unknown tool: {tool_name}"}

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })

                # 将工具执行结果加入上下文
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
                # 继续下一轮循环
                continue
            else:
                # 没有工具调用，提取最终文本并模拟流式输出
                final_text = ""
                for content in response.content:
                    if content.type == "text":
                        final_text += content.text

                chunk_size = 8
                for i in range(0, len(final_text), chunk_size):
                    yield f"data: {json.dumps({'text': final_text[i:i+chunk_size]})}\n\n"
                    time.sleep(0.01)
                break

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@login_required
@require_POST
def approve_proposal(request):
    """
    HTMX 确认排课接口。
    """
    student_id = request.POST.get("student_id")
    service_plan_id = request.POST.get("service_plan_id")
    start_at_str = request.POST.get("start_at")
    duration_hours_str = request.POST.get("duration_hours")

    if not all([student_id, service_plan_id, start_at_str, duration_hours_str]):
        return HttpResponse(
            '<div class="alert alert-danger m-0 py-2 small"><i class="bi bi-exclamation-triangle-fill"></i> 缺少必要参数</div>'
        )

    try:
        student = Student.objects.get(pk=student_id)
        service_plan = ServicePlan.objects.get(pk=service_plan_id)
    except (Student.DoesNotExist, ServicePlan.DoesNotExist):
        return HttpResponse(
            '<div class="alert alert-danger m-0 py-2 small"><i class="bi bi-exclamation-triangle-fill"></i> 学员或服务方案不存在</div>'
        )

    dt = parse_datetime(start_at_str)
    if not dt:
        return HttpResponse(
            '<div class="alert alert-danger m-0 py-2 small"><i class="bi bi-exclamation-triangle-fill"></i> 时间格式不正确</div>'
        )

    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())

    try:
        duration_hours = Decimal(duration_hours_str)
    except Exception:
        return HttpResponse(
            '<div class="alert alert-danger m-0 py-2 small"><i class="bi bi-exclamation-triangle-fill"></i> 时长格式不正确</div>'
        )

    # 创建排课记录
    schedule = Schedule(
        student=student,
        service_plan=service_plan,
        start_at=dt,
        duration_hours=duration_hours,
        owner=request.user,
        title=f"{student.name} - {service_plan.subject}"
    )

    try:
        schedule.full_clean()
        schedule.save()
        return HttpResponse(
            f'<div class="alert alert-success m-0 py-2 small"><i class="bi bi-check-circle-fill"></i> 排课成功！已安排：{schedule.title}，时间：{timezone.localtime(schedule.start_at).strftime("%Y-%m-%d %H:%M")}</div>'
        )
    except ValidationError as e:
        error_msg = "; ".join([f"{k}: {', '.join(v)}" for k, v in e.message_dict.items()])
        return HttpResponse(
            f'<div class="alert alert-danger m-0 py-2 small"><i class="bi bi-exclamation-triangle-fill"></i> 排课失败：{error_msg}</div>'
        )
    except Exception as e:
        return HttpResponse(
            f'<div class="alert alert-danger m-0 py-2 small"><i class="bi bi-exclamation-triangle-fill"></i> 排课失败：{str(e)}</div>'
        )


@login_required
@require_POST
def reject_proposal(request):
    """
    HTMX 拒绝排课接口。
    """
    return HttpResponse(
        '<div class="text-muted small"><i class="bi bi-x-circle"></i> 已取消该排课建议。</div>'
    )


@login_required
@require_POST
def generate_feedback(request):
    """
    根据排课记录和老师输入的草稿，调用大模型生成结构化的家长反馈。
    """
    schedule_id = request.POST.get("schedule_id")
    draft_text = request.POST.get("draft_text", "").strip()
    tone = request.POST.get("tone", "encouraging")

    if not schedule_id:
        return JsonResponse({"error": "缺少 schedule_id 参数"}, status=400)
    if not draft_text:
        return JsonResponse({"error": "请填写课堂草稿内容"}, status=400)

    try:
        # 获取排课与学员信息
        schedule = Schedule.objects.select_related("student").get(pk=schedule_id)
        student = schedule.student
    except Schedule.DoesNotExist:
        return JsonResponse({"error": "排课记录不存在"}, status=404)

    # 构造 Prompt 变量
    student_name = student.name
    student_tags = student.tags
    attention_note = student.attention_note

    system_prompt = get_feedback_system_prompt(
        tone=tone,
        student_name=student_name,
        student_tags=student_tags,
        attention_note=attention_note
    )
    user_message = get_feedback_user_message(draft_text)

    # 调用 AI 智能网关
    client = RobustAnthropicClient()
    try:
        response = client.call_with_prompt_cache(
            feature_name="generate_feedback",
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            input_params={
                "schedule_id": schedule_id,
                "tone": tone,
                "draft_length": len(draft_text)
            }
        )

        # 提取大模型返回的 JSON 字符串
        response_text = response.content[0].text.strip()

        # 尝试解析 JSON，确保其符合格式
        try:
            feedback_data = json.loads(response_text)
            return JsonResponse(feedback_data)
        except json.JSONDecodeError:
            # 如果大模型返回的不是纯 JSON，做一次后备清洗
            # 寻找第一个 '{' 和最后一个 '}'
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                cleaned_json = response_text[start_idx:end_idx + 1]
                feedback_data = json.loads(cleaned_json)
                return JsonResponse(feedback_data)
            else:
                return JsonResponse({"error": "AI 返回格式异常，未能解析为 JSON", "raw": response_text}, status=500)

    except Exception as e:
        return JsonResponse({"error": f"生成反馈失败: {str(e)}"}, status=500)


@login_required
def draft_payment_reminder(request):
    return JsonResponse({"status": "ok"})


def get_student_portrait_system_prompt(student_name: str, tags: str, attention_note: str) -> str:
    return f"""你是一位极其专业的教育心理学家和资深教师。
你的任务是根据学员的课后记录，生成一份客观、深入、有指导意义的“学员画像”。

【学员基本信息】
- 姓名：{student_name}
- 标签：{tags or "无"}
- 重点关注：{attention_note or "无"}

【输出格式要求】
请直接输出 HTML 格式的学员画像，不要包含 ```html 等 Markdown 标记，也不要包含任何前言或后记。
请使用以下 HTML 结构进行排版（保持简洁、专业）：
<div class="student-portrait">
    <div class="mb-3">
        <strong class="text-dark"><i class="bi bi-person-badge"></i> 学习特点与习惯：</strong>
        <p class="mb-1 text-secondary">{{学习特点与习惯的客观分析，结合课后记录，字数约 80-120 字}}</p>
    </div>
    <div class="mb-3">
        <strong class="text-dark"><i class="bi bi-exclamation-triangle"></i> 知识薄弱点：</strong>
        <p class="mb-1 text-secondary">{{梳理出的薄弱环节和摩擦点，字数约 80-120 字}}</p>
    </div>
    <div>
        <strong class="text-dark"><i class="bi bi-lightbulb"></i> 后续教学建议：</strong>
        <p class="mb-0 text-secondary">{{针对性的教学或辅导建议，字数约 80-120 字}}</p>
    </div>
</div>
"""


@login_required
def student_portrait(request):
    """
    根据课后备注生成 AI 学员画像。
    """
    student_id = request.GET.get("student_id")
    if not student_id:
        return HttpResponse("缺少 student_id 参数", status=400)

    student = get_object_or_404(Student, pk=student_id)
    notes = SessionNote.objects.filter(student=student).order_by("-created_at")

    if not notes.exists():
        return HttpResponse(
            '<div class="text-center py-3 text-muted"><i class="bi bi-info-circle"></i> 该学员暂无课后备注，无法生成画像。</div>'
        )

    # 编译最近的课堂记录作为上下文
    notes_summary = []
    for note in notes[:10]:
        date_str = note.created_at.strftime("%Y-%m-%d")
        notes_summary.append(f"【{date_str} 课堂记录】\\n情况：{note.summary}\\n下次重点：{note.next_focus}")

    notes_context = "\n\n".join(notes_summary)

    system_prompt = get_student_portrait_system_prompt(
        student_name=student.name,
        tags=student.tags,
        attention_note=student.attention_note
    )

    user_message = f"""请根据以下该学员最近的课堂记录，生成学员画像：

{notes_context}

请直接输出符合 HTML 格式的学员画像。"""

    client = RobustAnthropicClient()
    try:
        response = client.call_with_prompt_cache(
            feature_name="student_portrait",
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            input_params={"student_id": student_id, "notes_count": notes.count()}
        )

        response_text = response.content[0].text.strip()
        if response_text.startswith("```html"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        return HttpResponse(response_text)

    except Exception as e:
        return HttpResponse(
            f'<div class="text-danger small"><i class="bi bi-exclamation-circle"></i> 生成画像失败：{str(e)}</div>'
        )
