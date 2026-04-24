from typing import Any

from pydantic import BaseModel, Field

from app.schemas.chat import ArtifactItem, CitationItem


class InputBinding(BaseModel):
    from_step_no: int
    from_field: str
    to_param: str


class PlanStep(BaseModel):
    step_no: int
    capability_code: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    input_bindings: list[InputBinding] = Field(default_factory=list)


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
    citations: list[CitationItem] = Field(default_factory=list)
    artifacts: list[ArtifactItem] = Field(default_factory=list)
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
        for item in reversed(self.step_results):
            if item.success and item.structured_result:
                return item.structured_result
        return {}

    @property
    def aggregated_citations(self) -> list[CitationItem]:
        seen: set[tuple[str, str | None]] = set()
        result: list[CitationItem] = []
        for step in self.step_results:
            if step.success:
                for c in step.citations:
                    key = (c.source_type, c.title)
                    if key not in seen:
                        seen.add(key)
                        result.append(c)
        return result

    @property
    def aggregated_artifacts(self) -> list[ArtifactItem]:
        seen: set[tuple[str, str]] = set()
        result: list[ArtifactItem] = []
        for step in self.step_results:
            if not step.success:
                continue
            for a in step.artifacts:
                key = (a.artifact_type, a.name)
                if key in seen:
                    continue
                seen.add(key)
                result.append(a)
        return result

    @property
    def aggregated_raw_sql(self) -> str | None:
        for step in reversed(self.step_results):
            if step.success and step.raw_data.get("raw_sql"):
                return str(step.raw_data["raw_sql"])
        return None
