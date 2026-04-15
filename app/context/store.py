from app.schemas.context import SessionContext, SessionMessage, TaskContext


class InMemoryContextStore:
    """In-memory storage for session and task contexts"""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionContext] = {}
        self._tasks: dict[str, TaskContext] = {}

    def get_session(self, session_id: str) -> SessionContext:
        """Get or create session context"""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionContext(session_id=session_id)
        return self._sessions[session_id]

    def append_message(self, session_id: str, role: str, content: str) -> SessionContext:
        """Append message to session and keep last 10 messages"""
        session = self.get_session(session_id)
        session.recent_messages.append(SessionMessage(role=role, content=content))
        # Keep only last 10 messages to avoid unbounded growth
        session.recent_messages = session.recent_messages[-10:]
        return session

    def get_task(self, session_id: str) -> TaskContext:
        """Get or create task context for session"""
        if session_id not in self._tasks:
            self._tasks[session_id] = TaskContext(session_id=session_id)
        return self._tasks[session_id]

    def save_task(self, task: TaskContext) -> None:
        """Save or update task context"""
        self._tasks[task.session_id] = task
