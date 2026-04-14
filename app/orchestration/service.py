from typing import Any

from app.schemas.capability import CapabilityExecutionResult, ExecutionPlan, PlanExecutionResult

from .capability_mapper import CapabilityMapper
from .complexity import ComplexityEvaluator
from .decomposer import TaskDecomposer
from .intent_classifier import IntentClassifier
from .plan_builder import PlanBuilder
from .preprocessor import MessagePreprocessor
from .registry import CapabilityRegistry


class OrchestrationService:
    def __init__(self) -> None:
        self.preprocessor = MessagePreprocessor()
        self.intent_classifier = IntentClassifier()
        self.complexity = ComplexityEvaluator()
        self.decomposer = TaskDecomposer()
        self.mapper = CapabilityMapper()
        self.builder = PlanBuilder()
        self.registry = CapabilityRegistry()

    def plan(self, message: str) -> ExecutionPlan:
        features = self.preprocessor.parse(message)
        intent = self.intent_classifier.classify(features)
        is_multi = self.complexity.is_multi(features, intent)

        if not is_multi:
            step = self.decomposer.single_step(intent, message)
            mapped = self.mapper.map_single(step)
            return self.builder.build(intent, [mapped])

        steps = self.decomposer.multi_steps(intent, message)
        mapped = self.mapper.map_multi(steps)
        return self.builder.build(intent, mapped)

    def execute(self, plan: ExecutionPlan) -> PlanExecutionResult:
        step_results: list[CapabilityExecutionResult] = []
        latest_structured: dict[str, Any] = {}

        for step in plan.steps:
            payload = dict(step.input_data)
            payload["upstream"] = latest_structured

            handler = self.registry.get(step.capability_code)
            if not handler:
                step_results.append(
                    CapabilityExecutionResult(
                        step_no=step.step_no,
                        capability_code=step.capability_code,
                        success=False,
                        error=f"capability not implemented: {step.capability_code}",
                    )
                )
                continue

            try:
                result = handler.execute(step, payload)
            except Exception as exc:
                result = CapabilityExecutionResult(
                    step_no=step.step_no,
                    capability_code=step.capability_code,
                    success=False,
                    error=f"handler execution failed: {type(exc).__name__}: {exc}",
                )
            if result.success and result.structured_result:
                latest_structured = result.structured_result

            step_results.append(result)

        return PlanExecutionResult(
            plan_id=plan.plan_id,
            intent=plan.intent,
            step_results=step_results,
        )

    def run(self, message: str) -> PlanExecutionResult:
        plan = self.plan(message)
        return self.execute(plan)
