from concurrent.futures import ThreadPoolExecutor

from app.context.store import InMemoryContextStore
from app.orchestration.followup_resolver import FollowupResolver
from app.orchestration.service import OrchestrationService


def test_followup_resolver_detects_refine_request() -> None:
    resolver = FollowupResolver()
    assert resolver.is_followup("再正式一点") is True
    assert resolver.is_followup("改成发给领导的版本") is True
    assert resolver.is_followup("上个月哪个部门成本最高") is False


def test_followup_without_task_context_falls_back_to_normal_plan() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    plan = orchestration.plan("再正式一点", task_context=None)

    assert plan.intent != "content_followup"


def test_same_session_followup_reuses_previous_output() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    session_id = "sess_001"

    first = orchestration.run("根据采购审批要求，写一段说明", session_id=session_id)
    assert first.summary_text

    second = orchestration.run("再正式一点", session_id=session_id)

    assert second.intent == "content_followup"
    assert "现将有关情况说明如下" in second.summary_text


def test_followup_leader_version_generation() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    session_id = "sess_002"

    first = orchestration.run("帮我看上个月哪个部门成本最高", session_id=session_id)
    assert first.summary_text

    second = orchestration.run("改成发给领导的版本", session_id=session_id)

    assert second.intent == "content_from_previous_data"
    assert "领导您好" in second.summary_text


def test_knowledge_followup_to_content_generation() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    session_id = "sess_knowledge_to_content"

    first = orchestration.run("采购审批要求是什么", session_id=session_id)
    assert first.intent == "knowledge_only"

    second = orchestration.run("写成给员工看的解释", session_id=session_id)

    assert second.intent == "content_from_previous_knowledge"
    assert second.summary_text


def test_task_context_saves_followup_metadata() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    session_id = "sess_meta_001"

    orchestration.run("帮我看上个月哪个部门成本最高", session_id=session_id)
    task = store.get_task(session_id)

    assert task.important_outputs["latest_capability_code"] == "data.analyze"
    assert task.important_outputs["latest_output_type"] == "data"
    assert task.important_outputs["followup_ready"] is True


def test_task_context_saves_latest_user_message() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    session_id = "sess_latest_user_message"

    orchestration.run("帮我看上个月哪个部门成本最高", session_id=session_id)
    task = store.get_task(session_id)

    assert task.important_outputs["latest_user_message"] == "帮我看上个月哪个部门成本最高"


def test_data_continue_followup_runs_data_analyze() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    session_id = "sess_phase2_data"

    first = orchestration.run("帮我看上个月哪个部门成本最高", session_id=session_id)
    assert first.intent == "data_only"

    second = orchestration.run("换成同比", session_id=session_id)

    assert second.intent == "data_followup"
    assert second.step_results[0].capability_code == "data.analyze"


def test_knowledge_continue_followup_runs_knowledge_ask() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    session_id = "sess_phase2_knowledge"

    first = orchestration.run("采购审批要求是什么", session_id=session_id)
    assert first.intent == "knowledge_only"

    second = orchestration.run("补充审批节点", session_id=session_id)

    assert second.intent == "knowledge_followup"
    assert second.step_results[0].capability_code == "knowledge.ask"


def test_followup_rewrite_new_version() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    session_id = "sess_003"

    first = orchestration.run("根据采购审批要求，写一段说明", session_id=session_id)
    assert first.summary_text

    second = orchestration.run("再写一版", session_id=session_id)

    assert second.intent == "content_followup"
    assert "现重新表述如下" in second.summary_text


def test_followup_with_empty_previous_text_falls_back_to_normal_plan() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    session_id = "sess_004"
    task = store.get_task(session_id)
    task.important_outputs = {
        "latest_structured_result": {"value": 520000},
        "latest_summary_text": "",
    }
    store.save_task(task)

    result = orchestration.run("再正式一点", session_id=session_id)

    assert result.intent != "content_followup"


def test_context_store_returns_isolated_copies() -> None:
    store = InMemoryContextStore()

    task = store.get_task("sess_isolated")
    task.latest_intent = "tampered"
    task.important_outputs["latest_summary_text"] = "tampered"

    stored_task = store.get_task("sess_isolated")

    assert stored_task.latest_intent is None
    assert stored_task.important_outputs == {}


def test_update_task_preserves_original_state_when_updater_raises() -> None:
    store = InMemoryContextStore()
    store.update_task(
        "sess_rollback",
        lambda task: task.important_outputs.update({"counter": 1}),
    )

    def raising_updater(task) -> None:
        task.latest_intent = "should_not_persist"
        task.important_outputs["counter"] = 2
        raise ValueError("boom")

    try:
        store.update_task("sess_rollback", raising_updater)
    except ValueError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("expected ValueError")

    stored_task = store.get_task("sess_rollback")

    assert stored_task.latest_intent is None
    assert stored_task.important_outputs["counter"] == 1


def test_update_task_is_atomic_under_concurrent_updates() -> None:
    store = InMemoryContextStore()
    session_id = "sess_concurrent"
    update_count = 40

    def increment_counter() -> None:
        def updater(task) -> None:
            current = task.important_outputs.get("counter", 0)
            task.important_outputs["counter"] = current + 1

        store.update_task(session_id, updater)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(increment_counter) for _ in range(update_count)]
        for future in futures:
            future.result()

    stored_task = store.get_task(session_id)

    assert stored_task.important_outputs["counter"] == update_count
