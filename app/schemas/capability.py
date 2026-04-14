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


class CapabilityExecutionResult(BaseModel):
    step_no: int
    capability_code: str
    success: bool
    human_readable_text: str | None = None
    structured_result: dict[str, Any] = Field(default_factory=dict)
    raw_data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class PlanExecutionResult(BaseModel):
    plan_id: str
    intent: str
    step_results: list[CapabilityExecutionResult] = Field(default_factory=list)

    @property
    def summary_text(self) -> str:
        for item in reversed(self.step_results):
            if item.success and item.human_readable_text:
                return item.human_readable_text
        return "执行完成，但暂无可展示的结果。"

    @property
    def merged_structured_result(self) -> dict[str, Any]:
        for item in self.step_results:
            if item.success and item.structured_result:
                return item.structured_result
        return {}
