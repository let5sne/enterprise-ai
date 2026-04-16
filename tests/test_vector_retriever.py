"""Integration tests for VectorRetriever and index_builder against an
ephemeral Chroma collection. Skipped cleanly if ``chromadb`` isn't installed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

chromadb = pytest.importorskip("chromadb")

from app.knowledge.index_builder import build_index, chunk_markdown, extract_title
from app.knowledge.retriever import VectorRetriever
from app.knowledge.service import KnowledgeService


def test_chunk_markdown_splits_on_blank_lines() -> None:
    text = "para one\n\npara two\n\n  \n\npara three"
    chunks = chunk_markdown(text)
    assert chunks == ["para one", "para two", "para three"]


def test_chunk_markdown_splits_oversized_paragraph() -> None:
    long_para = "x" * 1800
    chunks = chunk_markdown(long_para, max_chars=800)
    assert len(chunks) == 3
    assert all(len(c) <= 800 for c in chunks)


def test_extract_title_from_first_heading() -> None:
    assert extract_title("# 采购审批\n\ncontent", fallback="fallback") == "采购审批"
    assert extract_title("no heading here", fallback="fallback") == "fallback"


def test_build_index_and_vector_retriever_roundtrip(tmp_path: Path, fake_embedding_client) -> None:
    # Seed two markdown docs.
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "policy_a.md").write_text(
        "# 采购审批\n\n采购需先提交申请再按金额区间走审批流程。", encoding="utf-8"
    )
    (docs_dir / "policy_b.md").write_text(
        "# 年假管理\n\n年假按司龄核定，需提前在系统申请并审批。", encoding="utf-8"
    )

    persist = tmp_path / "chroma"
    total = build_index(
        docs_dir=docs_dir,
        persist_path=str(persist),
        collection_name="test_kb",
        embedding_client=fake_embedding_client,
    )
    assert total >= 2

    retriever = VectorRetriever(
        collection_name="test_kb",
        persist_path=str(persist),
        embedding_client=fake_embedding_client,
    )
    results = retriever.retrieve("采购审批流程是什么", top_k=2)

    assert results
    top = results[0]
    assert top["source_type"] == "vector_doc"
    assert top["title"]
    assert "source_path" not in top or top["source"]  # source comes from meta
    assert isinstance(top["score"], float)


def test_knowledge_service_uses_injected_vector_retriever_and_llm(
    tmp_path: Path, fake_embedding_client, fake_llm_client
) -> None:
    """End-to-end: vector retriever + LLM synthesizer. Bypasses global settings
    by injecting both dependencies directly."""
    from app.knowledge.citations import CitationBuilder

    # Build a tiny index.
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "proc.md").write_text(
        "# 采购审批\n\n采购需先提交申请再按金额区间走审批流程。", encoding="utf-8"
    )
    persist = tmp_path / "chroma"
    build_index(
        docs_dir=docs_dir,
        persist_path=str(persist),
        collection_name="svc_kb",
        embedding_client=fake_embedding_client,
    )

    retriever = VectorRetriever(
        collection_name="svc_kb",
        persist_path=str(persist),
        embedding_client=fake_embedding_client,
    )

    # Force the LLM synthesis path without flipping global settings:
    # monkey-patch settings.llm_enabled for this call-site.
    from app.config import settings

    original = settings.llm_enabled
    settings.llm_enabled = True
    try:
        service = KnowledgeService(retriever=retriever, llm_client=fake_llm_client)
        service.citation_builder = CitationBuilder()

        answer, structured = service.ask("采购怎么审批")
    finally:
        settings.llm_enabled = original

    assert answer == "FAKE_LLM_OUTPUT"
    assert fake_llm_client.calls
    prompt = fake_llm_client.calls[0]["prompt"]
    assert "采购怎么审批" in prompt
    assert "采购需先提交申请" in prompt  # retrieved chunk injected

    citations = structured["citations"]
    assert citations
    assert citations[0].source_type == "vector_doc"
    assert citations[0].locator  # source_path populated


def test_knowledge_service_falls_back_when_llm_synthesis_empty(
    tmp_path: Path, fake_embedding_client
) -> None:
    """Empty LLM response → service falls back to template answer prefix."""
    from app.config import settings

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "proc.md").write_text(
        "# 采购审批\n\n采购需先提交申请再按金额区间走审批流程。", encoding="utf-8"
    )
    persist = tmp_path / "chroma"
    build_index(
        docs_dir=docs_dir,
        persist_path=str(persist),
        collection_name="fallback_kb",
        embedding_client=fake_embedding_client,
    )

    retriever = VectorRetriever(
        collection_name="fallback_kb",
        persist_path=str(persist),
        embedding_client=fake_embedding_client,
    )

    class EmptyLLM:
        def complete(self, *a, **kw):
            return ""

    original = settings.llm_enabled
    settings.llm_enabled = True
    try:
        service = KnowledgeService(retriever=retriever, llm_client=EmptyLLM())
        answer, _ = service.ask("采购怎么审批")
    finally:
        settings.llm_enabled = original

    assert answer.startswith("根据制度资料")
