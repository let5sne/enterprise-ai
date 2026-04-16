"""
TASK-005: API response contract tests
验证统一响应协议中各顶层字段、citations、artifacts、task_context、debug 的完整性。
"""
import pytest
from pydantic import ValidationError

from app.orchestration.service import OrchestrationService
from app.schemas.capability import PlanExecutionResult
from app.schemas.chat import (
    ArtifactItem,
    ChatAskResponse,
    CitationItem,
    ResponseDebugInfo,
    TaskContextSnapshot,
)


# ---------------------------------------------------------------------------
# Schema 单元测试
# ---------------------------------------------------------------------------


def test_citation_item_fields() -> None:
    c = CitationItem(
        source_type="memory_doc",
        title="采购审批制度",
        locator="section: 审批要求",
        snippet="采购审批应按金额分级审批……",
    )
    assert c.source_type == "memory_doc"
    assert c.title == "采购审批制度"
    assert c.locator == "section: 审批要求"
    assert c.snippet is not None


def test_citation_item_optional_fields() -> None:
    c = CitationItem(source_type="memory_doc")
    assert c.title is None
    assert c.locator is None
    assert c.snippet is None


def test_artifact_item_table() -> None:
    a = ArtifactItem(
        artifact_type="table",
        name="analysis_result",
        content=[{"department": "市场部", "value": 520000}],
    )
    assert a.artifact_type == "table"
    assert isinstance(a.content, list)
    assert a.content[0]["department"] == "市场部"  # type: ignore[index]


def test_artifact_item_text() -> None:
    a = ArtifactItem(artifact_type="text", name="summary", content="这是一段摘要")
    assert a.artifact_type == "text"
    assert isinstance(a.content, str)


def test_task_context_snapshot_defaults() -> None:
    t = TaskContextSnapshot()
    assert t.status == "completed"
    assert t.task_type is None
    assert t.summary is None
    assert t.important_outputs == {}


def test_response_debug_info() -> None:
    d = ResponseDebugInfo(
        intent="data_only",
        plan_steps=["data.analyze"],
        raw_sql="SELECT 1",
    )
    assert d.intent == "data_only"
    assert "data.analyze" in d.plan_steps
    assert d.raw_sql == "SELECT 1"


def test_chat_ask_response_has_required_fields() -> None:
    resp = ChatAskResponse(
        session_id="sess_abc",
        answer="这是答案",
        capabilities_used=["data.analyze"],
        trace_id="trace_xyz",
    )
    assert resp.session_id == "sess_abc"
    assert resp.answer == "这是答案"
    assert resp.capabilities_used == ["data.analyze"]
    assert resp.trace_id == "trace_xyz"
    assert resp.citations == []
    assert resp.artifacts == []
    assert resp.task_context is None
    assert resp.debug is None
    assert resp.contract_version == "v1"


def test_chat_ask_response_contract_version_literal() -> None:
    with pytest.raises(ValidationError):
        ChatAskResponse(
            contract_version="v2",  # type: ignore[arg-type]
            session_id="sess_abc",
            answer="答案",
            capabilities_used=[],
            trace_id="trace_xyz",
        )


def test_chat_ask_response_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ChatAskResponse.model_validate(
            {
                "session_id": "sess_abc",
                "answer": "答案",
                "capabilities_used": ["knowledge.ask"],
                "trace_id": "trace_xyz",
                "unknown_field": "boom",
            }
        )


def test_chat_ask_response_with_all_fields() -> None:
    resp = ChatAskResponse(
        session_id="sess_abc",
        answer="答案",
        capabilities_used=["knowledge.ask"],
        citations=[CitationItem(source_type="memory_doc", title="规章制度")],
        artifacts=[ArtifactItem(artifact_type="table", name="t1", content=[])],
        task_context=TaskContextSnapshot(task_type="knowledge_only", status="completed"),
        trace_id="trace_xyz",
        debug=ResponseDebugInfo(intent="knowledge_only", plan_steps=["knowledge.ask"]),
    )
    assert len(resp.citations) == 1
    assert resp.citations[0].title == "规章制度"
    assert len(resp.artifacts) == 1
    assert resp.task_context is not None
    assert resp.task_context.task_type == "knowledge_only"
    assert resp.debug is not None
    assert resp.debug.intent == "knowledge_only"


def test_artifact_item_literal_values() -> None:
    ArtifactItem(artifact_type="table", name="a")
    ArtifactItem(artifact_type="text", name="a")
    ArtifactItem(artifact_type="chart", name="a")
    ArtifactItem(artifact_type="file", name="a")

    with pytest.raises(ValidationError):
        ArtifactItem(artifact_type="json", name="a")  # type: ignore[arg-type]


def test_task_context_status_literal() -> None:
    TaskContextSnapshot(status="completed")
    with pytest.raises(ValidationError):
        TaskContextSnapshot(status="running")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# PlanExecutionResult 聚合测试
# ---------------------------------------------------------------------------


def test_plan_result_aggregates_citations() -> None:
    orchestration = OrchestrationService()
    result: PlanExecutionResult = orchestration.run("报销流程是什么")

    assert result.intent == "knowledge_only"
    citations = result.aggregated_citations
    assert isinstance(citations, list)
    assert len(citations) > 0
    assert all(isinstance(c, CitationItem) for c in citations)
    assert citations[0].source_type == "memory_doc"


def test_plan_result_aggregates_artifacts() -> None:
    orchestration = OrchestrationService()
    result: PlanExecutionResult = orchestration.run("上个月哪个部门成本最高")

    assert result.intent == "data_only"
    artifacts = result.aggregated_artifacts
    assert isinstance(artifacts, list)
    assert len(artifacts) > 0
    assert artifacts[0].artifact_type == "table"
    assert artifacts[0].name == "analysis_result"


def test_plan_result_aggregated_raw_sql() -> None:
    orchestration = OrchestrationService()
    result: PlanExecutionResult = orchestration.run("上个月哪个部门成本最高")

    raw_sql = result.aggregated_raw_sql
    assert raw_sql is not None
    assert isinstance(raw_sql, str)
    assert len(raw_sql) > 0


def test_plan_result_no_citations_for_data_only() -> None:
    orchestration = OrchestrationService()
    result: PlanExecutionResult = orchestration.run("上个月哪个部门成本最高")

    # data.analyze does not produce citations
    assert result.aggregated_citations == []


def test_plan_result_no_artifacts_for_knowledge_only() -> None:
    orchestration = OrchestrationService()
    result: PlanExecutionResult = orchestration.run("报销流程是什么")

    # knowledge.ask does not produce artifacts (no rows in structured_result)
    assert result.aggregated_artifacts == []


def test_plan_result_aggregates_across_multiple_steps() -> None:
    orchestration = OrchestrationService()
    result: PlanExecutionResult = orchestration.run("帮我看上个月哪个部门成本最高，并写一段说明")

    assert result.intent == "data_plus_content"
    assert len(result.step_results) == 2

    # data step produces artifacts
    artifacts = result.aggregated_artifacts
    assert len(artifacts) > 0

    # raw_sql comes from data step
    assert result.aggregated_raw_sql is not None


# ---------------------------------------------------------------------------
# API 端到端 contract 测试（通过 TestClient）
# ---------------------------------------------------------------------------


def test_api_response_top_level_fields(client) -> None:
    payload = {"user_id": "u1", "source": "web", "message": "报销流程是什么"}
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert "contract_version" in data
    assert data["contract_version"] == "v1"
    assert "session_id" in data
    assert "answer" in data
    assert "capabilities_used" in data
    assert "citations" in data
    assert "artifacts" in data
    assert "task_context" in data
    assert "trace_id" in data
    assert "debug" in data


def test_api_response_citations_for_knowledge(client) -> None:
    payload = {"user_id": "u1", "source": "web", "message": "报销流程是什么"}
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data["citations"], list)
    assert len(data["citations"]) > 0
    first = data["citations"][0]
    assert "source_type" in first
    assert first["source_type"] == "memory_doc"


def test_api_response_artifacts_for_data(client) -> None:
    payload = {"user_id": "u1", "source": "web", "message": "上个月哪个部门成本最高"}
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data["artifacts"], list)
    assert len(data["artifacts"]) > 0
    first = data["artifacts"][0]
    assert first["artifact_type"] == "table"
    assert "content" in first


def test_api_response_task_context_shape(client) -> None:
    payload = {"user_id": "u1", "source": "web", "message": "报销流程是什么"}
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200

    tc = resp.json()["task_context"]
    assert tc is not None
    assert tc["status"] == "completed"
    assert "task_type" in tc
    assert "important_outputs" in tc


def test_api_response_debug_contains_raw_sql_for_data(client) -> None:
    payload = {"user_id": "u1", "source": "web", "message": "上个月哪个部门成本最高"}
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200

    debug = resp.json()["debug"]
    assert debug is not None
    assert debug["raw_sql"] is not None
    assert isinstance(debug["raw_sql"], str)


def test_api_response_debug_intent_matches(client) -> None:
    payload = {"user_id": "u1", "source": "web", "message": "报销流程是什么"}
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200

    debug = resp.json()["debug"]
    assert debug["intent"] == "knowledge_only"
    assert "knowledge.ask" in debug["plan_steps"]


def test_api_response_answer_always_present(client) -> None:
    payload = {"user_id": "u1", "source": "web", "message": "采购审批流程是什么"}
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["answer"]
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0


# ---------------------------------------------------------------------------
# task_context 真实快照测试（非推断值）
# ---------------------------------------------------------------------------


def test_api_task_context_reflects_real_task_for_data(client) -> None:
    payload = {"user_id": "u1", "source": "web", "message": "上个月哪个部门成本最高"}
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200

    tc = resp.json()["task_context"]
    assert tc["task_type"] == "data_only"
    outputs = tc["important_outputs"]
    assert outputs["latest_output_type"] == "data"
    assert outputs["latest_capability_code"] == "data.analyze"
    assert outputs["followup_ready"] is True
    assert tc["summary"]


def test_api_task_context_reflects_real_task_for_knowledge(client) -> None:
    payload = {"user_id": "u1", "source": "web", "message": "报销流程是什么"}
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200

    tc = resp.json()["task_context"]
    assert tc["task_type"] == "knowledge_only"
    outputs = tc["important_outputs"]
    assert outputs["latest_output_type"] == "knowledge"
    assert outputs["latest_capability_code"] == "knowledge.ask"
    assert outputs["followup_ready"] is True


def test_api_task_context_does_not_leak_heavy_fields(client) -> None:
    payload = {"user_id": "u1", "source": "web", "message": "上个月哪个部门成本最高"}
    resp = client.post("/api/v1/chat/ask", json=payload)
    assert resp.status_code == 200

    outputs = resp.json()["task_context"]["important_outputs"]
    # lightweight snapshot must not expose raw structured data or user message
    assert "latest_structured_result" not in outputs
    assert "latest_user_message" not in outputs
    assert "latest_summary_text" not in outputs
