from typing import Any, Protocol

from app.schemas.capability import CapabilityExecutionResult, PlanStep


class CapabilityHandler(Protocol):
    capability_code: str

    def execute(self, step: PlanStep, payload: dict[str, Any]) -> CapabilityExecutionResult:
        ...
