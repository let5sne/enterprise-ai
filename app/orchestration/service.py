from typing import Any
from uuid import uuid4

from app.context.store import InMemoryContextStore
from app.schemas.capability import CapabilityExecutionResult, ExecutionPlan, PlanExecutionResult, PlanStep
from app.schemas.context import TaskContext

from .capability_mapper import CapabilityMapper
from .complexity import ComplexityEvaluator
from .decomposer import TaskDecomposer
from .followup_resolver import FollowupResolver
from .followup_type_classifier import FollowupTypeClassifier
from .followup_types import FollowupType
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
        self.followup_resolver = FollowupResolver()
        self.followup_type_classifier = FollowupTypeClassifier()
        self.context_store = context_store or InMemoryContextStore()

    def plan(self, message: str, task_context: TaskContext | None = None) -> ExecutionPlan:
        if self.followup_resolver.should_resume(message, task_context):
            return self._build_followup_plan(message, task_context)

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


    def run(self, message: str, session_id: str | None = None) -> PlanExecutionResult:
        task_context = self.context_store.get_task(session_id) if session_id else None

        if session_id:
            self.context_store.append_message(session_id, "user", message)

        plan = self.plan(message=message, task_context=task_context)
        result = self.execute(plan)

        if session_id:
            self._update_task_context_after_run(session_id, plan, result, message)
            self.context_store.append_message(session_id, "assistant", result.summary_text)

        return result


    def _build_followup_plan(
        self,
        message: str,
        task_context: TaskContext | None,
    ) -> ExecutionPlan:
        followup_type = self.followup_type_classifier.classify(message, task_context)
        important_outputs = (task_context.important_outputs if task_context else {}) or {}

        latest_structured_result = important_outputs.get("latest_structured_result", {}) or {}
        latest_summary_text = important_outputs.get("latest_summary_text", "") or ""
        latest_user_message = important_outputs.get("latest_user_message", "") or ""

        if followup_type == FollowupType.DATA_CONTINUE:
            merged_question = self._merge_followup_question(
                message=message,
                latest_user_message=latest_user_message,
                latest_summary_text=latest_summary_text,
                domain="data",
            )
            return ExecutionPlan(
                plan_id=f"plan_{uuid4().hex[:12]}",
                intent="data_followup",
                steps=[
                    PlanStep(
                        step_no=1,
                        capability_code="data.analyze",
                        input_data={"text": merged_question},
                    )
                ],
            )

        if followup_type == FollowupType.KNOWLEDGE_CONTINUE:
            merged_question = self._merge_followup_question(
                message=message,
                latest_user_message=latest_user_message,
                latest_summary_text=latest_summary_text,
                domain="knowledge",
            )
            return ExecutionPlan(
                plan_id=f"plan_{uuid4().hex[:12]}",
                intent="knowledge_followup",
                steps=[
                    PlanStep(
                        step_no=1,
                        capability_code="knowledge.ask",
                        input_data={"text": merged_question},
                    )
                ],
            )

        if followup_type == FollowupType.CONTENT_FROM_PREVIOUS_DATA:
            intent = "content_from_previous_data"
        elif followup_type == FollowupType.CONTENT_FROM_PREVIOUS_KNOWLEDGE:
            intent = "content_from_previous_knowledge"
        else:
            intent = "content_followup"

        return ExecutionPlan(
            plan_id=f"plan_{uuid4().hex[:12]}",
            intent=intent,
            steps=[
                PlanStep(
                    step_no=1,
                    capability_code="content.generate",
                    input_data={
                        "text": message,
                        "upstream": latest_structured_result,
                        "previous_text": latest_summary_text,
                        "followup_type": followup_type,
                    },
                )
            ],
        )

    def _update_task_context_after_run(
        self,
        session_id: str,
        plan: ExecutionPlan,
        result: PlanExecutionResult,
        source_message: str,
    ) -> None:
        task = self.context_store.get_task(session_id)

        latest_success_capability_code = None
        for step_result in reversed(result.step_results):
            if step_result.success:
                latest_success_capability_code = step_result.capability_code
                break

        real_summary_text = None
        for step_result in reversed(result.step_results):
            if step_result.success and step_result.human_readable_text:
                real_summary_text = step_result.human_readable_text
                break

        task.latest_intent = plan.intent
        task.latest_plan_id = plan.plan_id
        task.last_successful_step_no = max(
            (step.step_no for step in result.step_results if step.success),
            default=0,
        )
        task.important_outputs = {
            "latest_user_message": source_message,
            "latest_structured_result": result.merged_structured_result,
            "latest_summary_text": real_summary_text,
            "latest_capability_code": latest_success_capability_code,
            "latest_output_type": self._resolve_output_type(latest_success_capability_code),
            "followup_ready": bool(latest_success_capability_code and real_summary_text),
        }
        self.context_store.save_task(task)

    def _merge_followup_question(
        self,
        message: str,
        latest_user_message: str,
        latest_summary_text: str,
        domain: str,
    ) -> str:
        base = latest_user_message.strip() or latest_summary_text.strip()
        if not base:
            return message
        if domain == "data":
            return f"基于刚才的数据分析需求“{base}”，请继续按这个要求处理：{message}"
        if domain == "knowledge":
            return f"基于刚才的制度/规则问题“{base}”，请继续补充说明：{message}"
        return f"基于刚才的内容“{base}”，请继续处理：{message}"

    def _resolve_output_type(self, capability_code: str | None) -> str:
        if capability_code == "content.generate":
            return "content"
        if capability_code == "data.analyze":
            return "data"
        if capability_code == "knowledge.ask":
            return "knowledge"
        return ""


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
