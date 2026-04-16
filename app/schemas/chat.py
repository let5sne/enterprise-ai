from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ChatAskRequest(BaseModel):
    session_id: str | None = None
    user_id: str
    source: Literal["web", "openclaw", "feishu", "wecom", "api"]
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message cannot be empty")
        return normalized


class CitationItem(BaseModel):
    source_type: str
    title: str | None = None
    locator: str | None = None
    snippet: str | None = None


class ArtifactItem(BaseModel):
    artifact_type: str
    name: str
    content: list[Any] | dict[str, Any] | str | None = None


class TaskContextSnapshot(BaseModel):
    task_type: str | None = None
    status: str = "completed"
    summary: str | None = None
    important_outputs: dict[str, Any] = Field(default_factory=dict)


class ResponseDebugInfo(BaseModel):
    intent: str | None = None
    plan_steps: list[str] = Field(default_factory=list)
    raw_sql: str | None = None


class ChatAskResponse(BaseModel):
    session_id: str
    answer: str
    capabilities_used: list[str] = Field(default_factory=list)
    citations: list[CitationItem] = Field(default_factory=list)
    artifacts: list[ArtifactItem] = Field(default_factory=list)
    task_context: TaskContextSnapshot | None = None
    trace_id: str
    debug: ResponseDebugInfo | None = None
