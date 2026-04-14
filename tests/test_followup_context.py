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

    first = orchestration.run("帮我看上个月哪个部门成本最高，并写一段说明", session_id=session_id)
    assert first.summary_text

    second = orchestration.run("改成发给领导的版本", session_id=session_id)

    assert second.intent == "content_followup"
    assert "领导您好" in second.summary_text


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
