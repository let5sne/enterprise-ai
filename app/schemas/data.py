from typing import Any, Literal

from pydantic import BaseModel, Field


class DataQueryIntent(BaseModel):
    metric: str | None = None
    dimension: str | None = None
    time_range: str | None = None
    analysis_type: Literal["metric", "ranking", "comparison", "unknown"] = "unknown"
    original_question: str


class DataAnalysisResult(BaseModel):
    success: bool
    summary_text: str | None = None
    structured_result: dict[str, Any] = Field(default_factory=dict)
    raw_sql: str | None = None
    error: str | None = None
