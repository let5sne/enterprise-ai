import json
import logging
from typing import Any

from app.llm import prompts as llm_prompts
from app.llm.client import LLMClient

logger = logging.getLogger(__name__)


class TemplateContentGenerator:
    """Deterministic, rule- and template-based content generator.

    Used as the default path when LLM is disabled, and as a safety-net
    fallback inside LLMContentGenerator when the LLM call fails.
    """

    FOLLOWUP_KEYWORDS = (
        "继续",
        "再正式一点",
        "更正式一点",
        "再简短一点",
        "更简短一点",
        "再写一版",
        "换个更口语化的版本",
        "改成发给领导的版本",
        "帮我润色一下",
        "再优化一下",
    )

    def generate(
        self,
        instruction: str,
        source_data: dict | None = None,
        previous_text: str | None = None,
    ) -> str:
        source_data = source_data or {}
        previous_text = (previous_text or "").strip()
        normalized = instruction.strip()

        # Prefer refinement against previous output when available.
        if previous_text:
            if "再正式一点" in normalized or "更正式一点" in normalized:
                return f"现将有关情况说明如下：{previous_text}"

            if "再简短一点" in normalized or "更简短一点" in normalized:
                return f"简要说明：{previous_text}"

            if "发给领导" in normalized or "领导" in normalized:
                return f"领导您好，现将有关情况简要汇报如下：{previous_text}"

            if "润色" in normalized or "优化" in normalized:
                return f"经优化后的表述如下：{previous_text}"

            if "再写一版" in normalized:
                return f"现重新表述如下：{previous_text}"

            if "口语化" in normalized:
                return f"下面给你一个更口语化的版本：{previous_text}"

            if "继续" in normalized:
                return previous_text

        if any(keyword in normalized for keyword in self.FOLLOWUP_KEYWORDS):
            return "抱歉，我没有找到可供调整的上一轮输出，请先让我生成一版初稿。"

        if "top_item" in source_data and "value" in source_data:
            return (
                f"根据分析结果，{source_data['top_item']}为关键关注对象，"
                f"当前数值为{source_data['value']}。建议围绕该对象进一步拆解原因与改进动作。"
            )

        if "difference" in source_data and "ratio_percent" in source_data:
            return (
                f"本期较上期变化{source_data['difference']}，环比{source_data['ratio_percent']}%。"
                "建议结合业务活动与成本结构进一步归因。"
            )

        if "value" in source_data:
            return f"当前查询结果为{source_data['value']}。建议结合历史区间继续观察趋势。"

        if "answer" in source_data:
            return f"根据已有资料，建议表述为：{source_data['answer']}"

        return f"基于你的需求，我先给出说明草稿：{instruction}。"


class LLMContentGenerator:
    """LLM-backed generator. On any failure falls back to TemplateContentGenerator."""

    def __init__(
        self,
        llm_client: LLMClient,
        fallback: TemplateContentGenerator | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.fallback = fallback or TemplateContentGenerator()

    def _build_prompt(
        self,
        instruction: str,
        source_data: dict[str, Any],
        previous_text: str,
    ) -> str:
        if previous_text:
            return llm_prompts.CONTENT_REFINE_TEMPLATE.format(
                instruction=instruction,
                previous_text=previous_text,
            )

        if source_data:
            # Route to knowledge-flavored prompt when upstream looks like a
            # knowledge answer (has "answer" or "citations"); otherwise treat
            # it as analytical data.
            is_knowledge = "answer" in source_data or "citations" in source_data
            template = (
                llm_prompts.CONTENT_FROM_KNOWLEDGE_TEMPLATE
                if is_knowledge
                else llm_prompts.CONTENT_FROM_DATA_TEMPLATE
            )
            return template.format(
                instruction=instruction,
                source_data=json.dumps(source_data, ensure_ascii=False, indent=2, default=str),
            )

        return llm_prompts.CONTENT_PLAIN_TEMPLATE.format(instruction=instruction)

    def generate(
        self,
        instruction: str,
        source_data: dict | None = None,
        previous_text: str | None = None,
    ) -> str:
        instr = (instruction or "").strip()
        src = source_data or {}
        prev = (previous_text or "").strip()

        prompt = self._build_prompt(instr, src, prev)
        try:
            text = self.llm_client.complete(prompt, system=llm_prompts.CONTENT_SYSTEM)
            if text and text.strip():
                return text.strip()
            logger.warning("LLM returned empty content; falling back to template.")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("LLM content generation failed (%s); falling back to template.", exc)

        return self.fallback.generate(
            instruction=instruction,
            source_data=source_data,
            previous_text=previous_text,
        )


# Backward compatibility alias: existing `from .generator import ContentGenerator`
ContentGenerator = TemplateContentGenerator


__all__ = [
    "ContentGenerator",
    "TemplateContentGenerator",
    "LLMContentGenerator",
]
