from typing import Any

from app.data import DataService
from app.schemas.capability import CapabilityExecutionResult, PlanStep


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
            return CapabilityExecutionResult(
                step_no=step.step_no,
                capability_code=step.capability_code,
                success=True,
                human_readable_text=result.summary_text,
                structured_result=result.structured_result,
                raw_data={"raw_sql": result.raw_sql},
            )

        return CapabilityExecutionResult(
            step_no=step.step_no,
            capability_code=step.capability_code,
            success=False,
            error=result.error,
            raw_data={"raw_sql": result.raw_sql} if result.raw_sql else {},
        )
