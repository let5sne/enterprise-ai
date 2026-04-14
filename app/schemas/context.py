from typing import Any

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """Placeholder for future user/session context orchestration input."""

    user_id: str | None = None
    session_id: str | None = None
    source: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class SessionMessage(BaseModel):
    """Single message in a conversation"""

    role: str  # "user", "assistant"
    content: str


class SessionContext(BaseModel):
    """Conversation context within a session"""

    session_id: str
    recent_messages: list[SessionMessage] = Field(default_factory=list)


class TaskContext(BaseModel):
    """Task execution context tied to a session"""

    session_id: str
    latest_intent: str | None = None
    latest_plan_id: str | None = None
    last_successful_step_no: int | None = None
    important_outputs: dict[str, Any] = Field(default_factory=dict)
