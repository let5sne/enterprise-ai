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


class ChatAskResponse(BaseModel):
    session_id: str
    answer: str
    capabilities_used: list[str] = Field(default_factory=list)
    trace_id: str
    structured_result: dict[str, Any] = Field(default_factory=dict)
