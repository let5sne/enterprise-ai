from typing import Any

from app.schemas.capability import CapabilityExecutionResult, ExecutionPlan, PlanExecutionResult, PlanStep

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
        step_results_by_no: dict[int, CapabilityExecutionResult] = {}
        latest_structured: dict[str, Any] = {}

        for step in plan.steps:
            payload = dict(step.input_data)
            binding_error = self._apply_input_bindings(step, payload, step_results_by_no)
            if binding_error:
                result = CapabilityExecutionResult(
                    step_no=step.step_no,
                    capability_code=step.capability_code,
                    success=False,
                    error=binding_error,
                )
                step_results.append(result)
                step_results_by_no[step.step_no] = result
                continue

            if "upstream" not in payload:
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
            step_results_by_no[step.step_no] = result

        return PlanExecutionResult(
            plan_id=plan.plan_id,
            intent=plan.intent,
            step_results=step_results,
        )

    def run(self, message: str) -> PlanExecutionResult:
        plan = self.plan(message)
        return self.execute(plan)

    def _apply_input_bindings(
        self,
        step: PlanStep,
        payload: dict[str, Any],
        step_results_by_no: dict[int, CapabilityExecutionResult],
    ) -> str | None:
        for binding in step.input_bindings:
            source_result = step_results_by_no.get(binding.from_step_no)
            if source_result is None:
                return (
                    f"input binding failed: source step not found "
                    f"(step={step.step_no}, from_step_no={binding.from_step_no})"
                )

            if not source_result.success:
                return (
                    f"input binding failed: source step unsuccessful "
                    f"(step={step.step_no}, from_step_no={binding.from_step_no})"
                )

            bound_value, error = self._extract_binding_value(source_result, binding.from_field)
            if error:
                return (
                    f"input binding failed: {error} "
                    f"(step={step.step_no}, from_step_no={binding.from_step_no})"
                )

            payload[binding.to_param] = bound_value

        return None

    def _extract_binding_value(
        self, source_result: CapabilityExecutionResult, from_field: str
    ) -> tuple[Any, str | None]:
        if from_field == "structured_result":
            return source_result.structured_result, None

        if from_field == "human_readable_text":
            return source_result.human_readable_text, None

        if from_field == "raw_data":
            return source_result.raw_data, None

        if from_field.startswith("structured_result."):
            value: Any = source_result.structured_result
            for key in from_field.split(".")[1:]:
                if not isinstance(value, dict) or key not in value:
                    return None, f"binding field not found: {from_field}"
                value = value[key]
            return value, None

        return None, f"unsupported binding field: {from_field}"
