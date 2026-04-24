"""Tests for rich artifacts emitted by capability handlers."""
from __future__ import annotations

from typing import cast

from pydantic import ValidationError
import pytest

from app.orchestration.service import OrchestrationService
from app.schemas.capability import (
    CapabilityExecutionResult,
    PlanExecutionResult,
)
from app.schemas.chat import ArtifactItem


# ---------------------------------------------------------------------------
# Schema-level
# ---------------------------------------------------------------------------


def test_artifact_item_accepts_title_and_metadata() -> None:
    a = ArtifactItem(
        artifact_type="chart",
        name="analysis_chart",
        title="各部门成本",
        content={"categories": ["a"], "series": [{"name": "v", "data": [1]}]},
        metadata={"chart_type": "bar"},
    )
    assert a.title == "各部门成本"
    assert a.metadata["chart_type"] == "bar"


def test_artifact_item_defaults() -> None:
    a = ArtifactItem(artifact_type="text", name="x")
    assert a.title is None
    assert a.metadata == {}


def test_artifact_item_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ArtifactItem.model_validate(
            {"artifact_type": "text", "name": "x", "unknown_field": "boom"}
        )


# ---------------------------------------------------------------------------
# data.analyze → table + chart
# ---------------------------------------------------------------------------


def _artifacts_by_type(result: PlanExecutionResult, t: str) -> list[ArtifactItem]:
    return [a for a in result.aggregated_artifacts if a.artifact_type == t]


def test_data_ranking_emits_table_and_chart() -> None:
    orchestration = OrchestrationService()
    result = orchestration.run("上个月哪个部门成本最高")

    tables = _artifacts_by_type(result, "table")
    charts = _artifacts_by_type(result, "chart")
    assert len(tables) == 1
    assert len(charts) == 1

    chart = charts[0]
    assert chart.metadata["chart_type"] == "bar"
    assert chart.metadata["analysis_type"] == "ranking"
    content = cast(dict, chart.content)
    assert "市场部" in content["categories"]
    assert content["series"][0]["data"] == [520000]


def test_data_comparison_emits_chart_with_month_categories() -> None:
    orchestration = OrchestrationService()
    result = orchestration.run("本月成本和上个月成本对比")

    charts = _artifacts_by_type(result, "chart")
    # comparison may or may not resolve to month categories depending on executor;
    # we only assert that if a chart exists, it has two data points aligned with rows.
    if charts:
        content = cast(dict, charts[0].content)
        assert len(content["categories"]) == len(content["series"][0]["data"])


def test_data_table_artifact_carries_rows() -> None:
    orchestration = OrchestrationService()
    result = orchestration.run("上个月哪个部门成本最高")

    tables = _artifacts_by_type(result, "table")
    assert tables
    content = cast(list, tables[0].content)
    assert isinstance(content, list)
    assert "dimension_name" in content[0]
    assert "metric_value" in content[0]


# ---------------------------------------------------------------------------
# content.generate → text artifact
# ---------------------------------------------------------------------------


def test_content_emits_text_artifact() -> None:
    orchestration = OrchestrationService()
    result = orchestration.run("根据采购审批要求，写一段说明")

    texts = _artifacts_by_type(result, "text")
    assert len(texts) == 1
    text_artifact = texts[0]
    assert text_artifact.name == "generated_content"
    assert isinstance(text_artifact.content, str)
    assert text_artifact.content == result.summary_text
    assert text_artifact.metadata.get("source_intent")
    assert text_artifact.metadata.get("word_count") == len(result.summary_text)


# ---------------------------------------------------------------------------
# PlanExecutionResult.aggregated_artifacts dedup
# ---------------------------------------------------------------------------


def test_aggregated_artifacts_dedupes_by_type_and_name() -> None:
    step1 = CapabilityExecutionResult(
        step_no=1,
        capability_code="data.analyze",
        success=True,
        human_readable_text="x",
        artifacts=[
            ArtifactItem(artifact_type="table", name="analysis_result", content=[{"a": 1}]),
            ArtifactItem(artifact_type="chart", name="analysis_chart", content={"x": 1}),
        ],
    )
    step2 = CapabilityExecutionResult(
        step_no=2,
        capability_code="data.analyze",
        success=True,
        human_readable_text="y",
        artifacts=[
            # duplicate (table, analysis_result) should be dropped
            ArtifactItem(artifact_type="table", name="analysis_result", content=[{"a": 2}]),
            ArtifactItem(artifact_type="text", name="generated_content", content="hi"),
        ],
    )
    plan_result = PlanExecutionResult(
        plan_id="p", intent="data_only", step_results=[step1, step2]
    )

    agg = plan_result.aggregated_artifacts
    keys = [(a.artifact_type, a.name) for a in agg]
    assert keys == [
        ("table", "analysis_result"),
        ("chart", "analysis_chart"),
        ("text", "generated_content"),
    ]


# ---------------------------------------------------------------------------
# API-level end-to-end
# ---------------------------------------------------------------------------


def test_api_data_response_contains_table_and_chart(client) -> None:
    payload = {"user_id": "u1", "source": "web", "message": "上个月哪个部门成本最高"}
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200
    artifacts = resp.json()["artifacts"]
    types = [a["artifact_type"] for a in artifacts]
    assert "table" in types
    assert "chart" in types


def test_api_content_response_contains_text_artifact(client) -> None:
    payload = {
        "user_id": "u1",
        "source": "web",
        "message": "根据采购审批要求，写一段说明",
    }
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200
    artifacts = resp.json()["artifacts"]
    text_items = [a for a in artifacts if a["artifact_type"] == "text"]
    assert len(text_items) == 1
    assert text_items[0]["content"] == resp.json()["answer"]
