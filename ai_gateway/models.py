import uuid
from django.db import models


class AIAuditLog(models.Model):
    """
    AI 接口调用审计日志，用于监控 Token 消耗、缓存效率、响应耗时和实际成本。
    """
    trace_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, verbose_name="链路追踪ID")
    feature_name = models.CharField(max_length=64, db_index=True, verbose_name="功能模块")
    input_parameters = models.JSONField(default=dict, blank=True, verbose_name="输入参数")
    raw_prompt = models.TextField(verbose_name="原始提示词")
    raw_response = models.TextField(verbose_name="原始响应内容")

    # Token 统计
    input_tokens = models.PositiveIntegerField(default=0, verbose_name="输入Token数")
    output_tokens = models.PositiveIntegerField(default=0, verbose_name="输出Token数")
    input_tokens_cached = models.PositiveIntegerField(default=0, verbose_name="缓存命中Token数")

    # 性能与成本
    latency_ms = models.PositiveIntegerField(verbose_name="响应耗时(毫秒)")
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0.0, verbose_name="预估成本(USD)")
    cache_hit_rate = models.FloatField(default=0.0, verbose_name="缓存命中率")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="调用时间")

    class Meta:
        verbose_name = "AI 审计日志"
        verbose_name_plural = "AI 审计日志"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # 动态计算 Anthropic Claude 3.5 Sonnet 的成本:
        # 基础输入: $3/M tokens, 缓存输入: $0.30/M tokens, 输出: $15/M tokens
        uncached_input_tokens = self.input_tokens - self.input_tokens_cached
        uncached_price = uncached_input_tokens * 3.0 / 1000000.0
        cached_price = self.input_tokens_cached * 0.30 / 1000000.0
        output_price = self.output_tokens * 15.0 / 1000000.0

        self.cost_usd = uncached_price + cached_price + output_price

        if self.input_tokens > 0:
            self.cache_hit_rate = float(self.input_tokens_cached) / float(self.input_tokens)
        else:
            self.cache_hit_rate = 0.0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.feature_name} - {self.trace_id} ({self.latency_ms}ms)"
