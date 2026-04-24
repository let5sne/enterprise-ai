from app.context.store import InMemoryContextStore
from app.schemas.context import TaskContext


class FakeClock:
    def __init__(self) -> None:
        self.current = 0.0

    def now(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def test_default_store_disables_ttl() -> None:
    clock = FakeClock()
    store = InMemoryContextStore(time_provider=clock.now)

    store.append_message("sess_default", "user", "hello")
    clock.advance(10_000)

    session = store.get_session("sess_default")

    assert len(session.recent_messages) == 1
    assert session.recent_messages[0].content == "hello"


def test_expired_session_returns_fresh_context() -> None:
    clock = FakeClock()
    store = InMemoryContextStore(ttl_seconds=5, time_provider=clock.now)

    store.append_message("sess_expired", "user", "hello")
    clock.advance(6)

    session = store.get_session("sess_expired")

    assert session.session_id == "sess_expired"
    assert session.recent_messages == []


def test_expired_task_returns_fresh_context() -> None:
    clock = FakeClock()
    store = InMemoryContextStore(ttl_seconds=5, time_provider=clock.now)

    store.save_task(
        TaskContext(
            session_id="task_expired",
            latest_intent="data_only",
            important_outputs={"latest_summary_text": "hello"},
        )
    )
    clock.advance(6)

    task = store.get_task("task_expired")

    assert task.session_id == "task_expired"
    assert task.latest_intent is None
    assert task.important_outputs == {}


def test_update_task_refreshes_expiry_window() -> None:
    clock = FakeClock()
    store = InMemoryContextStore(ttl_seconds=5, time_provider=clock.now)

    store.save_task(TaskContext(session_id="task_refresh"))
    clock.advance(3)
    store.update_task(
        "task_refresh",
        lambda task: task.important_outputs.update({"counter": 1}),
    )
    clock.advance(3)

    task = store.get_task("task_refresh")

    assert task.important_outputs["counter"] == 1


def test_cleanup_removes_expired_entries() -> None:
    clock = FakeClock()
    store = InMemoryContextStore(ttl_seconds=5, time_provider=clock.now)

    store.append_message("sess_1", "user", "hello")
    store.save_task(TaskContext(session_id="task_1", latest_intent="content_only"))
    clock.advance(6)

    store.cleanup()

    assert store._sessions == {}
    assert store._tasks == {}
