from typing import Any

from app.content import ContentService
from app.schemas.capability import CapabilityExecutionResult, PlanStep


class ContentGenerateHandler:
    capability_code = "content.generate"

    def __init__(self) -> None:
        self.content_service = ContentService()

    def execute(self, step: PlanStep, payload: dict[str, Any]) -> CapabilityExecutionResult:
        try:
            text, structured = self.content_service.generate(
                instruction=str(payload.get("text", "")),
                source_data=payload.get("upstream") or {},
                previous_text=str(payload.get("previous_text", "") or ""),
            )
        except Exception as exc:
            return CapabilityExecutionResult(
                step_no=step.step_no,
                capability_code=step.capability_code,
                success=False,
                error=f"execution error: {exc}",
            )

        return CapabilityExecutionResult(
            step_no=step.step_no,
            capability_code=step.capability_code,
            success=True,
            human_readable_text=text,
            structured_result=structured,
            raw_data={"source": "content_service"},
        )
