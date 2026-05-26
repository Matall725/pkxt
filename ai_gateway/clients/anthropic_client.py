import logging
import time
from django.conf import settings
from anthropic import Anthropic, APIConnectionError, APIStatusError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ..models import AIAuditLog

logger = logging.getLogger(__name__)


class RobustAnthropicClient:
    """
    具备指数退避重试、Prompt Caching 和自动审计日志记录的 Anthropic 客户端。
    """
    def __init__(self, api_key: str = None):
        # 优先使用传入的 api_key，否则从 Django settings 中读取
        self.api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", None)
        if not self.api_key:
            # 允许在测试或本地未配置时优雅降级，不直接崩溃
            logger.warning("ANTHROPIC_API_KEY is not configured. AI features will be disabled.")
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIConnectionError, APIStatusError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Anthropic API 调用失败，正在进行第 {retry_state.attempt_number} 次重试..."
        )
    )
    def call_with_prompt_cache(self, feature_name: str, system_prompt: str, messages: list, tools: list = None, input_params: dict = None):
        """
        调用 Claude 3.5 Sonnet，并启用提示词缓存与审计日志记录。
        """
        if not self.client:
            raise ValueError("Anthropic 客户端未初始化，请配置 ANTHROPIC_API_KEY")

        # 构造请求参数，对系统提示词启用缓存
        kwargs = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2048,
            "system": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}  # 缓存系统提示词
                }
            ],
            "messages": messages
        }

        # 如果有工具定义，也对其启用缓存
        if tools:
            cached_tools = []
            for tool in tools:
                tool_copy = tool.copy()
                tool_copy["cache_control"] = {"type": "ephemeral"}  # 缓存工具定义
                cached_tools.append(tool_copy)
            kwargs["tools"] = cached_tools

        start_time = time.time()
        try:
            # 在较新版本的 anthropic SDK 中，prompt caching 已经合并到 beta.messages 中
            response = self.client.beta.messages.create(**kwargs)
            latency_ms = int((time.time() - start_time) * 1000)

            # 提取 Token 使用情况
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            # 提取缓存命中 Token 数 (Anthropic 特有字段)
            input_tokens_cached = getattr(response.usage, "cache_read_input_tokens", 0)

            # 异步/后台保存审计日志（这里直接保存，Django 中通常足够快）
            AIAuditLog.objects.create(
                feature_name=feature_name,
                input_parameters=input_params or {},
                raw_prompt=f"System: {system_prompt}\nMessages: {messages}",
                raw_response=str(response.content),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                input_tokens_cached=input_tokens_cached,
                latency_ms=latency_ms
            )

            return response

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"AI Gateway 调用失败 [{feature_name}]: {str(e)}")
            # 记录失败日志
            AIAuditLog.objects.create(
                feature_name=feature_name,
                input_parameters=input_params or {},
                raw_prompt=f"System: {system_prompt}\nMessages: {messages}",
                raw_response=f"Error: {str(e)}",
                input_tokens=0,
                output_tokens=0,
                input_tokens_cached=0,
                latency_ms=latency_ms
            )
            raise e
