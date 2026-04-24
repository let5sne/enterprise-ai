from collections.abc import Callable
from threading import RLock
from time import monotonic

from app.schemas.context import SessionContext, SessionMessage, TaskContext


class InMemoryContextStore:
    """In-memory storage for session and task contexts.

    Expiration is lazy on hot paths: an accessed session/task is dropped only
    when that specific key has expired. Call ``cleanup()`` to proactively purge
    all expired entries.
    """

    def __init__(
        self,
        ttl_seconds: float | None = None,
        time_provider: Callable[[], float] | None = None,
    ) -> None:
        self._sessions: dict[str, SessionContext] = {}
        self._tasks: dict[str, TaskContext] = {}
        self._session_access_times: dict[str, float] = {}
        self._task_access_times: dict[str, float] = {}
        self._lock = RLock()
        self._ttl_seconds = ttl_seconds
        self._time_provider = time_provider or monotonic

    def get_session(self, session_id: str) -> SessionContext:
        """Get or create session context"""
        with self._lock:
            self._expire_session_if_needed_locked(session_id)
            session = self._get_or_create_session_locked(session_id)
            self._session_access_times[session_id] = self._now()
            return session.model_copy(deep=True)

    def append_message(self, session_id: str, role: str, content: str) -> SessionContext:
        """Append message to session and keep last 10 messages"""
        with self._lock:
            self._expire_session_if_needed_locked(session_id)
            session = self._get_or_create_session_locked(session_id)
            session.recent_messages.append(SessionMessage(role=role, content=content))
            # Keep only last 10 messages to avoid unbounded growth
            session.recent_messages = session.recent_messages[-10:]
            self._session_access_times[session_id] = self._now()
            return session.model_copy(deep=True)

    def get_task(self, session_id: str) -> TaskContext:
        """Get or create task context for session"""
        with self._lock:
            self._expire_task_if_needed_locked(session_id)
            task = self._get_or_create_task_locked(session_id)
            self._task_access_times[session_id] = self._now()
            return task.model_copy(deep=True)

    def save_task(self, task: TaskContext) -> None:
        """Save or update task context"""
        with self._lock:
            self._expire_task_if_needed_locked(task.session_id)
            self._tasks[task.session_id] = task.model_copy(deep=True)
            self._task_access_times[task.session_id] = self._now()

    def update_task(self, session_id: str, updater: Callable[[TaskContext], None]) -> TaskContext:
        """Apply an in-place update while holding the store lock."""
        with self._lock:
            self._expire_task_if_needed_locked(session_id)
            task = self._get_or_create_task_locked(session_id)
            updated_task = task.model_copy(deep=True)
            updater(updated_task)
            self._tasks[session_id] = updated_task
            self._task_access_times[session_id] = self._now()
            return updated_task.model_copy(deep=True)

    def cleanup(self) -> None:
        """Remove expired entries when TTL is enabled."""
        with self._lock:
            self._purge_expired_locked()

    def clear(self) -> None:
        """Clear all in-memory state. Used by tests and local resets."""
        with self._lock:
            self._sessions.clear()
            self._tasks.clear()
            self._session_access_times.clear()
            self._task_access_times.clear()

    def _get_or_create_session_locked(self, session_id: str) -> SessionContext:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionContext(session_id=session_id)
        return self._sessions[session_id]

    def _get_or_create_task_locked(self, session_id: str) -> TaskContext:
        if session_id not in self._tasks:
            self._tasks[session_id] = TaskContext(session_id=session_id)
        return self._tasks[session_id]

    def _now(self) -> float:
        return self._time_provider()

    def _purge_expired_locked(self) -> None:
        if self._ttl_seconds is None:
            return

        now = self._now()
        expired_sessions = [
            session_id
            for session_id, last_accessed_at in self._session_access_times.items()
            if now - last_accessed_at >= self._ttl_seconds
        ]
        expired_tasks = [
            session_id
            for session_id, last_accessed_at in self._task_access_times.items()
            if now - last_accessed_at >= self._ttl_seconds
        ]

        for session_id in expired_sessions:
            self._sessions.pop(session_id, None)
            self._session_access_times.pop(session_id, None)

        for session_id in expired_tasks:
            self._tasks.pop(session_id, None)
            self._task_access_times.pop(session_id, None)

    def _expire_session_if_needed_locked(self, session_id: str) -> None:
        if not self._is_expired(self._session_access_times.get(session_id)):
            return

        self._sessions.pop(session_id, None)
        self._session_access_times.pop(session_id, None)

    def _expire_task_if_needed_locked(self, session_id: str) -> None:
        if not self._is_expired(self._task_access_times.get(session_id)):
            return

        self._tasks.pop(session_id, None)
        self._task_access_times.pop(session_id, None)

    def _is_expired(self, last_accessed_at: float | None) -> bool:
        if self._ttl_seconds is None or last_accessed_at is None:
            return False

        return self._now() - last_accessed_at >= self._ttl_seconds
