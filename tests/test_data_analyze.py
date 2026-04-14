from app.data.service import DataService
from app.orchestration.registry import CapabilityRegistry
from app.orchestration.service import OrchestrationService
from app.orchestration.intent_classifier import IntentClassifier
from app.orchestration.decomposer import TaskDecomposer
from app.orchestration.capability_mapper import CapabilityMapper
from app.schemas.capability import ExecutionPlan, InputBinding, PlanStep


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
    assert registry.get("knowledge.ask") is not None
    assert "data.analyze" in registry.list_codes()
    assert "content.generate" in registry.list_codes()
    assert "knowledge.ask" in registry.list_codes()


def test_orchestration_data_plus_content_chain() -> None:
    orchestration = OrchestrationService()
    plan = orchestration.plan("帮我看上个月哪个部门成本最高，并写一段说明")

    assert len(plan.steps) == 2
    assert plan.steps[1].input_bindings
    assert plan.steps[1].input_bindings[0].from_step_no == 1
    assert plan.steps[1].input_bindings[0].from_field == "structured_result"
    assert plan.steps[1].input_bindings[0].to_param == "upstream"

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
                capability_code="workflow.status",
                input_data={"text": "hello"},
            )
        ],
    )

    result = orchestration.execute(plan)

    assert len(result.step_results) == 1
    assert result.step_results[0].success is False
    assert "capability not implemented" in (result.step_results[0].error or "")


def test_execute_binding_source_not_found_returns_failed_step() -> None:
    orchestration = OrchestrationService()
    plan = ExecutionPlan(
        plan_id="p-test-binding-not-found",
        intent="data_plus_content",
        steps=[
            PlanStep(
                step_no=1,
                capability_code="content.generate",
                input_data={"text": "写一段说明"},
            ),
            PlanStep(
                step_no=2,
                capability_code="content.generate",
                input_data={"text": "继续写"},
                input_bindings=[
                    InputBinding(
                        from_step_no=99,
                        from_field="structured_result",
                        to_param="upstream",
                    )
                ],
            ),
        ],
    )

    result = orchestration.execute(plan)

    assert len(result.step_results) == 2
    assert result.step_results[0].success is True
    assert result.step_results[1].success is False
    assert "input binding failed" in (result.step_results[1].error or "")
    assert "source step not found" in (result.step_results[1].error or "")


def test_intent_classifier_recognizes_knowledge_plus_content() -> None:
    classifier = IntentClassifier()
    
    features = {
        "has_knowledge": True,
        "has_generate": True,
    }
    intent = classifier.classify(features)
    
    assert intent == "knowledge_plus_content"


def test_decomposer_splits_knowledge_plus_content() -> None:
    decomposer = TaskDecomposer()
    
    tasks = decomposer.multi_steps(
        "knowledge_plus_content",
        "根据采购审批要求，写一份采购计划说明"
    )
    
    assert len(tasks) == 2
    assert tasks[0]["type"] == "knowledge"
    assert tasks[1]["type"] == "content"
    assert tasks[0]["message"] == "根据采购审批要求，写一份采购计划说明"
    assert tasks[1]["message"] == "根据采购审批要求，写一份采购计划说明"


def test_orchestration_knowledge_plus_content_plan() -> None:
    orchestration = OrchestrationService()
    plan = orchestration.plan("根据采购审批要求，生成一份说明")
    
    assert len(plan.steps) == 2
    assert plan.steps[0].capability_code == "knowledge.ask"
    assert plan.steps[1].capability_code == "content.generate"
    assert plan.steps[1].input_bindings
    assert plan.steps[1].input_bindings[0].from_step_no == 1
    assert plan.steps[1].input_bindings[0].from_field == "structured_result"
    assert plan.steps[1].input_bindings[0].to_param == "upstream"


def test_orchestration_knowledge_plus_content_execution() -> None:
    orchestration = OrchestrationService()
    result = orchestration.run("根据采购审批要求，写一段面向员工的解释")
    
    assert len(result.step_results) == 2
    assert result.step_results[0].success is True
    assert result.step_results[1].success is True
    assert result.step_results[1].structured_result is not None
    assert "," in result.summary_text or "。" in result.summary_text
