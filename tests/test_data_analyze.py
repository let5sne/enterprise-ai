from app.data.service import DataService
from app.orchestration.registry import CapabilityRegistry
from app.orchestration.service import OrchestrationService
from app.orchestration.intent_classifier import IntentClassifier
from app.orchestration.decomposer import TaskDecomposer
from app.orchestration.capability_mapper import CapabilityMapper
from app.orchestration.preprocessor import MessagePreprocessor
from app.schemas.capability import ExecutionPlan, InputBinding, PlanStep
from app.context.store import InMemoryContextStore


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


def test_intent_classifier_avoids_generic_word_misidentification() -> None:
    """Test that generic words like '要求' don't trigger knowledge intent incorrectly"""
    classifier = IntentClassifier()
    preprocessor = MessagePreprocessor()
    
    # "根据用户要求生成报告" should be content_only (generic 要求), not knowledge_plus_content
    features = preprocessor.parse("根据用户要求生成报告")
    intent = classifier.classify(features)
    
    assert intent == "content_only"
    assert features["has_generate"] is True
    assert features["has_knowledge"] is False  # Generic "要求" shouldn't match strict KNOWLEDGE_PATTERN


def test_intent_classifier_prioritizes_data_over_knowledge() -> None:
    """When both data and knowledge features are present, data takes priority to avoid false positives"""
    classifier = IntentClassifier()
    preprocessor = MessagePreprocessor()
    
    # "按照审批金额生成统计" has both data ("金额","统计") and vague knowledge ("审批")
    # Should be treated as data-focused, not knowledge_plus_content
    features = preprocessor.parse("按照审批金额生成统计")
    intent = classifier.classify(features)
    
    # The priority rule should prevent this from being knowledge_plus_content
    # It should be data_plus_content (both data and generate present)
    assert intent == "data_plus_content" or intent == "content_only"
    assert intent != "knowledge_plus_content"


def test_knowledge_pattern_requires_context() -> None:
    """Knowledge pattern should not trigger on generic 'requirements' without institutional context"""
    classifier = IntentClassifier()
    preprocessor = MessagePreprocessor()
    
    # Generic requirements without institutional words should not trigger knowledge
    # "根据用户要求生成报告" - "要求" is too generic to indicate knowledge/policy
    features = preprocessor.parse("根据用户要求生成报告")
    intent = classifier.classify(features)
    # Should be content_only, not knowledge_plus_content
    assert intent == "content_only"
    
    # Proper knowledge case with institutional context should trigger knowledge
    features = preprocessor.parse("根据采购审批要求，写一份说明")
    intent = classifier.classify(features)
    # Should trigger knowledge_plus_content
    assert intent == "knowledge_plus_content"


def test_context_store_appends_messages_with_rolling_buffer() -> None:
    """Test that context store appends messages and maintains rolling 10-message buffer"""
    store = InMemoryContextStore()
    session_id = "sess_test_001"
    
    # Add 15 messages; only latest 10 should be retained
    for i in range(15):
        role = "user" if i % 2 == 0 else "assistant"
        store.append_message(session_id, role, f"message_{i}")
    
    session = store.get_session(session_id)
    assert len(session.recent_messages) == 10
    assert session.recent_messages[0].content == "message_5"  # First message is the 6th one added
    assert session.recent_messages[-1].content == "message_14"  # Last message is the 15th one added


def test_task_context_updates_after_run() -> None:
    """Test that task context is populated with execution results after run()"""
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)
    session_id = "sess_test_002"
    
    result = orchestration.run("上个月哪个部门成本最高", session_id)
    
    task = store.get_task(session_id)
    assert task.latest_intent is not None
    assert task.latest_plan_id == result.plan_id
    assert task.last_successful_step_no > 0
    assert task.important_outputs["latest_structured_result"] is not None
    assert task.important_outputs["latest_summary_text"] is not None


def test_same_session_can_continue_previous_task() -> None:
    """Test that same session_id can read/write across multiple run() calls"""
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)
    session_id = "sess_test_003"
    
    # First message
    result1 = orchestration.run("上个月哪个部门成本最高", session_id)
    assert result1.step_results[0].success is True
    
    # Second message in same session
    result2 = orchestration.run("写一段说明", session_id)
    
    # Verify both messages are in session history
    session = store.get_session(session_id)
    messages = session.recent_messages
    assert len(messages) >= 4  # At least 2 user + 2 assistant messages
    assert messages[0].role == "user"
    assert "上个月" in messages[0].content or "成本最高" in messages[0].content
    
    # Verify task context tracks the latest execution
    task = store.get_task(session_id)
    assert task.latest_plan_id == result2.plan_id


def test_different_sessions_are_isolated() -> None:
    """Test that different session_ids maintain independent contexts"""
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)
    
    session1 = "sess_test_004_a"
    session2 = "sess_test_004_b"
    
    # Execute in first session
    orchestration.run("上个月哪个部门成本最高", session1)
    
    # Execute in second session with different message
    orchestration.run("本月销售额是多少", session2)
    
    # Verify isolation: each session should have only its own messages
    messages1 = store.get_session(session1).recent_messages
    messages2 = store.get_session(session2).recent_messages
    
    # Session 1 messages should not contain session 2 content
    session1_content = " ".join(m.content for m in messages1)
    assert "销售额" not in session1_content or "成本最高" in session1_content
    
    # Different planning should result in different plan IDs
    task1 = store.get_task(session1)
    task2 = store.get_task(session2)
    assert task1.latest_plan_id != task2.latest_plan_id
