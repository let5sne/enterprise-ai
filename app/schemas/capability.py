from typing import Any

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    step_no: int
    capability_code: str
    input_data: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    plan_id: str
    intent: str
    steps: list[PlanStep]
