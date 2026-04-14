from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """Placeholder for future user/session context orchestration input."""

    user_id: str | None = None
    session_id: str | None = None
    source: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
