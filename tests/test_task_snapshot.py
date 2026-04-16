"""Unit tests for OrchestrationService.build_task_snapshot."""
from app.context.store import InMemoryContextStore
from app.orchestration.service import OrchestrationService


def test_build_task_snapshot_returns_none_without_session() -> None:
    orchestration = OrchestrationService()
    assert orchestration.build_task_snapshot(None) is None


def test_build_task_snapshot_reads_real_task_context() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    session_id = "sess_snapshot_data"
    orchestration.run("帮我看上个月哪个部门成本最高", session_id=session_id)

    snapshot = orchestration.build_task_snapshot(session_id)

    assert snapshot is not None
    assert snapshot.task_type == "data_only"
    assert snapshot.status == "completed"
    assert snapshot.summary
    assert snapshot.important_outputs["latest_output_type"] == "data"
    assert snapshot.important_outputs["latest_capability_code"] == "data.analyze"
    assert snapshot.important_outputs["followup_ready"] is True


def test_build_task_snapshot_is_lightweight() -> None:
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    session_id = "sess_snapshot_light"
    orchestration.run("上个月哪个部门成本最高", session_id=session_id)

    snapshot = orchestration.build_task_snapshot(session_id)

    assert snapshot is not None
    # heavy / PII fields must not be exposed via the snapshot
    assert "latest_structured_result" not in snapshot.important_outputs
    assert "latest_user_message" not in snapshot.important_outputs
    assert "latest_summary_text" not in snapshot.important_outputs


def test_build_task_snapshot_for_empty_session_returns_defaults() -> None:
    """When a session exists but no run has occurred, snapshot fields are empty."""
    store = InMemoryContextStore()
    orchestration = OrchestrationService(context_store=store)

    snapshot = orchestration.build_task_snapshot("sess_never_run")

    assert snapshot is not None
    assert snapshot.task_type is None
    assert snapshot.summary is None
    assert snapshot.important_outputs == {}
