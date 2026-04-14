from app.data.service import DataService
from app.orchestration.registry import CapabilityRegistry
from app.orchestration.service import OrchestrationService
from app.schemas.capability import ExecutionPlan, PlanStep


def test_data_analyze_ranking_top1() -> None:
    service = DataService()

    result = service.analyze("上个月哪个部门成本最高")

    assert result.success is True
    assert result.summary_text is not None
    assert "最高项" in result.summary_text
    assert result.structured_result["top_item"] == "市场部"


def test_data_analyze_metric_value() -> None:
    service = DataService()

    result = service.analyze("本月销售额是多少")

    assert result.success is True
    assert result.summary_text == "查询结果为 520000。"
    assert result.structured_result["value"] == 520000


def test_registry_resolves_known_capabilities() -> None:
    registry = CapabilityRegistry()

    assert registry.get("data.analyze") is not None
    assert registry.get("content.generate") is not None
    assert registry.get("knowledge.ask") is None
    assert "data.analyze" in registry.list_codes()
    assert "content.generate" in registry.list_codes()


def test_orchestration_data_plus_content_chain() -> None:
    orchestration = OrchestrationService()

    result = orchestration.run("帮我看上个月哪个部门成本最高，并写一段说明")

    assert result.intent == "data_plus_content"
    assert len(result.step_results) == 2
    assert result.step_results[0].capability_code == "data.analyze"
    assert result.step_results[0].success is True
    assert result.step_results[1].capability_code == "content.generate"
    assert result.step_results[1].success is True
    assert "市场部" in (result.step_results[1].human_readable_text or "")
    # merged_structured_result 应返回最后一步（content.generate）的结构化结果
    assert "content" in result.merged_structured_result


def test_execute_unknown_capability_returns_failed_step() -> None:
    orchestration = OrchestrationService()
    plan = ExecutionPlan(
        plan_id="p-test-unknown",
        intent="unknown",
        steps=[
            PlanStep(
                step_no=1,
                capability_code="knowledge.ask",
                input_data={"text": "hello"},
            )
        ],
    )

    result = orchestration.execute(plan)

    assert len(result.step_results) == 1
    assert result.step_results[0].success is False
    assert "capability not implemented" in (result.step_results[0].error or "")
