from app.knowledge import KnowledgeService
from app.orchestration.service import OrchestrationService


def test_knowledge_service_returns_answer_and_citations() -> None:
    service = KnowledgeService()

    answer, structured = service.ask("报销流程是什么")

    assert "根据制度资料" in answer
    assert isinstance(structured.get("citations"), list)
    assert len(structured.get("citations", [])) > 0


def test_knowledge_service_fallback_for_unknown_question() -> None:
    service = KnowledgeService()

    answer, structured = service.ask("这个问题和制度无关")

    assert "未命中专项制度" in answer
    assert structured.get("citations")
    assert structured["citations"][0]["source"] == "制度知识库-通用指引"


def test_orchestration_knowledge_only_chain() -> None:
    orchestration = OrchestrationService()

    result = orchestration.run("报销流程是什么")

    assert result.intent == "knowledge_only"
    assert len(result.step_results) == 1
    assert result.step_results[0].capability_code == "knowledge.ask"
    assert result.step_results[0].success is True
    assert "根据制度资料" in (result.step_results[0].human_readable_text or "")
