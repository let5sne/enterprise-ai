from typing import Any

from app.knowledge import KnowledgeService
from app.schemas.capability import CapabilityExecutionResult, PlanStep


class KnowledgeAskHandler:
    capability_code = "knowledge.ask"

    def __init__(self) -> None:
        self.knowledge_service = KnowledgeService()

    def execute(self, step: PlanStep, payload: dict[str, Any]) -> CapabilityExecutionResult:
        try:
            answer, structured = self.knowledge_service.ask(str(payload.get("text", "")))
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
            human_readable_text=answer,
            structured_result=structured,
            raw_data={"citations": structured.get("citations", []), "source": "knowledge_service"},
        )
