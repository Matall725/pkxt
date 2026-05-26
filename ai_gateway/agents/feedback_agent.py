import json
from pydantic import BaseModel, Field
from typing import List, Optional

# 定义家长反馈信的结构化 JSON Schema
class ParentFeedbackSchema(BaseModel):
    skills_covered: List[str] = Field(
        description="本节课覆盖的核心知识点或技能列表，例如：['一元二次方程求根公式', '因式分解的十字相乘法']"
    )
    performance_level: str = Field(
        description="对学生课堂表现和掌握情况的客观、具体的分析。字数在 100-150 字之间。"
    )
    struggles_identified: List[str] = Field(
        description="课堂上发现的学生薄弱环节、理解摩擦点或易错点。如果没有，可以为空列表。"
    )
    assigned_drills: List[str] = Field(
        description="布置的课后作业、针对性练习或复习建议，例如：['完成课后习题第3、4题', '复习公式并口默写一遍']"
    )
    encouragement: str = Field(
        description="针对性的、有温度的鼓励话术。必须结合学生的实际表现，拒绝空洞的套话。字数在 50-80 字之间。"
    )


# 语气预设模板
TONE_PRESETS = {
    "encouraging": "温和鼓励型：语气充满亲和力、耐心和鼓励，多肯定进步，用温和的方式指出不足，适合低年级或容易受挫的孩子。",
    "analytical": "严谨分析型：语气客观、专业、理性，用数据和具体表现说话，重点剖析逻辑漏洞，适合需要明确方向和提升空间的学生。",
    "exam_oriented": "应试提分型：语气紧迫、目标导向，紧扣考纲和得分点，强调做题速度、准确率和考试规范，适合面临重要考试的学生。"
}


def get_feedback_system_prompt(tone: str = "encouraging", student_name: str = "学生", student_tags: str = "", attention_note: str = "") -> str:
    """
    生成结构化的系统提示词，包含 Prompt Caching 优化的静态指令。
    """
    tone_instruction = TONE_PRESETS.get(tone, TONE_PRESETS["encouraging"])

    system_prompt = f"""你是一位极其专业、有责任心且深谙教育心理学的私人教师/咨询师。
你的任务是根据老师提供的简短课堂草稿，为家长撰写一份结构化、高质量的课后反馈报告。

【当前学生基本信息】
- 学生姓名：{student_name}
- 学生标签：{student_tags or "无"}
- 老师备注的注意事项：{attention_note or "无"}

【撰写语气要求】
请严格按照以下语气风格进行撰写：
{tone_instruction}

【输出格式要求】
你必须且只能输出一个符合以下 JSON 结构的字符串，不要包含任何 Markdown 标记（如 ```json），也不要包含任何前言或后记。

JSON 结构：
{{
    "skills_covered": ["知识点1", "知识点2"],
    "performance_level": "课堂表现与掌握情况的详细分析...",
    "struggles_identified": ["薄弱点1", "薄弱点2"],
    "assigned_drills": ["作业/复习建议1", "作业/复习建议2"],
    "encouragement": "有温度的鼓励话术..."
}}

【撰写原则】
1. 真实具体：结合老师输入的草稿，不要凭空捏造学生没做过的事情，但可以根据专业知识进行合理延伸（例如：讲了三角函数，可以延伸到对空间想象力的锻炼）。
2. 拒绝套话：鼓励话术必须结合学生本节课的具体表现或其个人标签（如：针对“粗心大意”的学生，鼓励他保持耐心的同时肯定他的敏捷思维）。
3. 严禁幻觉：如果老师的草稿中没有提到薄弱环节，"struggles_identified" 可以为空列表，不要强行编造。
"""
    return system_prompt


def get_feedback_user_message(draft_text: str) -> str:
    """
    生成用户输入消息。
    """
    return f"""请根据以下老师记录的课堂简短草稿，生成家长反馈报告：

【课堂草稿】
{draft_text}

请直接输出符合要求的 JSON 字符串。"""
