from typing import Any

from app.data import DataService
from app.schemas.capability import CapabilityExecutionResult, PlanStep
from app.schemas.chat import ArtifactItem


class DataAnalyzeHandler:
    capability_code = "data.analyze"

    def __init__(self) -> None:
        self.data_service = DataService()

    def execute(self, step: PlanStep, payload: dict[str, Any]) -> CapabilityExecutionResult:
        try:
            result = self.data_service.analyze(str(payload.get("text", "")))
        except Exception as exc:
            return CapabilityExecutionResult(
                step_no=step.step_no,
                capability_code=step.capability_code,
                success=False,
                error=f"execution error: {exc}",
            )

        if result.success:
            artifacts = self._build_artifacts(result.structured_result)
            return CapabilityExecutionResult(
                step_no=step.step_no,
                capability_code=step.capability_code,
                success=True,
                human_readable_text=result.summary_text,
                structured_result=result.structured_result,
                raw_data={"raw_sql": result.raw_sql},
                artifacts=artifacts,
            )

        return CapabilityExecutionResult(
            step_no=step.step_no,
            capability_code=step.capability_code,
            success=False,
            error=result.error,
            raw_data={"raw_sql": result.raw_sql} if result.raw_sql else {},
        )

    def _build_artifacts(self, structured_result: dict[str, Any]) -> list[ArtifactItem]:
        if not structured_result:
            return []

        rows = structured_result.get("rows")
        if rows and isinstance(rows, list):
            return [ArtifactItem(artifact_type="table", name="analysis_result", content=rows)]

        # flatten scalar structured result into a single-row table
        flat = {k: v for k, v in structured_result.items() if not isinstance(v, (dict, list))}
        if flat:
            return [ArtifactItem(artifact_type="table", name="analysis_result", content=[flat])]

        return []
