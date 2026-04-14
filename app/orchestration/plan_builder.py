import uuid

from app.schemas.capability import ExecutionPlan, PlanStep


class PlanBuilder:
    def build(self, intent: str, steps: list[PlanStep]) -> ExecutionPlan:
        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            intent=intent,
            steps=steps,
        )
