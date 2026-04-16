"""Tests for LLMContentGenerator prompt construction and fallback behavior."""
from __future__ import annotations

from app.content.generator import LLMContentGenerator, TemplateContentGenerator
from app.content.service import ContentService
from app.llm import prompts as llm_prompts


def test_llm_generator_uses_refine_prompt_when_previous_text(fake_llm_client) -> None:
    gen = LLMContentGenerator(llm_client=fake_llm_client)

    out = gen.generate(
        instruction="再正式一点",
        previous_text="市场部本月成本最高。",
    )

    assert out == "FAKE_LLM_OUTPUT"
    assert len(fake_llm_client.calls) == 1
    call = fake_llm_client.calls[0]
    assert "再正式一点" in call["prompt"]
    assert "市场部本月成本最高" in call["prompt"]
    assert call["system"] == llm_prompts.CONTENT_SYSTEM
    # Refine template, not data template
    assert "【上一版文本】" in call["prompt"]


def test_llm_generator_uses_data_prompt_when_source_data(fake_llm_client) -> None:
    gen = LLMContentGenerator(llm_client=fake_llm_client)

    out = gen.generate(
        instruction="写一段说明",
        source_data={"top_item": "市场部", "value": 98000},
    )

    assert out == "FAKE_LLM_OUTPUT"
    prompt = fake_llm_client.calls[0]["prompt"]
    assert "【结构化数据】" in prompt
    assert "市场部" in prompt
    assert "98000" in prompt


def test_llm_generator_uses_knowledge_prompt_when_answer_upstream(fake_llm_client) -> None:
    gen = LLMContentGenerator(llm_client=fake_llm_client)

    gen.generate(
        instruction="写一段说明",
        source_data={"answer": "采购需先申请再审批"},
    )

    prompt = fake_llm_client.calls[0]["prompt"]
    assert "【知识资料】" in prompt
    assert "采购需先申请再审批" in prompt


def test_llm_generator_plain_prompt_without_upstream(fake_llm_client) -> None:
    gen = LLMContentGenerator(llm_client=fake_llm_client)

    gen.generate(instruction="帮我写一段开场白")

    prompt = fake_llm_client.calls[0]["prompt"]
    assert "帮我写一段开场白" in prompt
    assert "【上一版文本】" not in prompt
    assert "【结构化数据】" not in prompt
    assert "【知识资料】" not in prompt


def test_llm_generator_falls_back_on_empty_response(fake_llm_client) -> None:
    fake_llm_client.response = "   "  # empty after strip
    gen = LLMContentGenerator(llm_client=fake_llm_client)

    out = gen.generate(
        instruction="写一段说明",
        source_data={"top_item": "市场部", "value": 98000},
    )

    # Should fall back to TemplateContentGenerator output
    assert "市场部" in out
    assert "98000" in out


def test_llm_generator_falls_back_on_exception() -> None:
    class BoomClient:
        def complete(self, *a, **kw):
            raise RuntimeError("connection refused")

    gen = LLMContentGenerator(llm_client=BoomClient())
    out = gen.generate(
        instruction="写一段说明",
        source_data={"top_item": "市场部", "value": 98000},
    )
    assert "市场部" in out


def test_content_service_injects_generator(fake_llm_client) -> None:
    """ContentService honors injected generator regardless of settings."""
    gen = LLMContentGenerator(llm_client=fake_llm_client)
    service = ContentService(generator=gen)

    text, structured = service.generate(
        instruction="写一段说明",
        source_data={"top_item": "市场部", "value": 98000},
    )

    assert text == "FAKE_LLM_OUTPUT"
    assert structured["content"] == "FAKE_LLM_OUTPUT"
    assert fake_llm_client.calls


def test_template_generator_backward_compatible_alias() -> None:
    """The old ``ContentGenerator`` name is preserved as an alias."""
    from app.content.generator import ContentGenerator

    assert ContentGenerator is TemplateContentGenerator
