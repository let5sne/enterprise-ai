from typing import Any

from app.context.store import InMemoryContextStore
from app.schemas.capability import CapabilityExecutionResult, ExecutionPlan, PlanExecutionResult, PlanStep

from .capability_mapper import CapabilityMapper
from .complexity import ComplexityEvaluator
from .decomposer import TaskDecomposer
from .intent_classifier import IntentClassifier
from .plan_builder import PlanBuilder
from .preprocessor import MessagePreprocessor
from .registry import CapabilityRegistry


class OrchestrationService:
    def __init__(self, context_store: InMemoryContextStore | None = None) -> None:
        self.preprocessor = MessagePreprocessor()
        self.intent_classifier = IntentClassifier()
        self.complexity = ComplexityEvaluator()
        self.decomposer = TaskDecomposer()
        self.mapper = CapabilityMapper()
        self.builder = PlanBuilder()
        self.registry = CapabilityRegistry()
        self.context_store = context_store or InMemoryContextStore()

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

    def execute(self, plan: ExecutionPlan, session_id: str | None = None) -> PlanExecutionResult:
        step_results: list[CapabilityExecutionResult] = []
        step_results_by_no: dict[int, CapabilityExecutionResult] = {}
        latest_structured: dict[str, Any] = {}
        latest_summary: str | None = None

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
            if result.success and result.human_readable_text:
                latest_summary = result.human_readable_text

            step_results.append(result)
            step_results_by_no[step.step_no] = result

        result = PlanExecutionResult(
            plan_id=plan.plan_id,
            intent=plan.intent,
            step_results=step_results,
        )

        # Persist context if session_id provided
        if session_id:
            task = self.context_store.get_task(session_id)
            task.latest_intent = plan.intent
            task.latest_plan_id = plan.plan_id
            task.last_successful_step_no = max(
                (step.step_no for step in step_results if step.success),
                default=0,
            )
            task.important_outputs = {
                "latest_structured_result": latest_structured,
                "latest_summary_text": latest_summary,
            }
            self.context_store.save_task(task)

        return result


    def run(self, message: str, session_id: str | None = None) -> PlanExecutionResult:
        # Append user message to session context if session_id provided
        if session_id:
            self.context_store.append_message(session_id, "user", message)

        plan = self.plan(message)
        result = self.execute(plan, session_id)

        # Append assistant response summary to session context
        if session_id and result.step_results:
            last_step = result.step_results[-1]
            summary = (
                last_step.human_readable_text
                or last_step.structured_result
                or "Execution completed"
            )
            self.context_store.append_message(session_id, "assistant", str(summary))

        return result


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
