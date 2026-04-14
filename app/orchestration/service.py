from typing import Any

from app.data import DataService
from app.schemas.capability import CapabilityExecutionResult, ExecutionPlan, PlanExecutionResult

from .capability_mapper import CapabilityMapper
from .complexity import ComplexityEvaluator
from .decomposer import TaskDecomposer
from .intent_classifier import IntentClassifier
from .plan_builder import PlanBuilder
from .preprocessor import MessagePreprocessor


class OrchestrationService:
    def __init__(self) -> None:
        self.preprocessor = MessagePreprocessor()
        self.intent_classifier = IntentClassifier()
        self.complexity = ComplexityEvaluator()
        self.decomposer = TaskDecomposer()
        self.mapper = CapabilityMapper()
        self.builder = PlanBuilder()
        self.data_service = DataService()

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

            if step.capability_code == "data.analyze":
                try:
                    result = self.data_service.analyze(str(payload.get("text", "")))
                except Exception as exc:
                    step_results.append(
                        CapabilityExecutionResult(
                            step_no=step.step_no,
                            capability_code=step.capability_code,
                            success=False,
                            error=f"execution error: {exc}",
                        )
                    )
                    continue

                if result.success:
                    latest_structured = result.structured_result
                    step_results.append(
                        CapabilityExecutionResult(
                            step_no=step.step_no,
                            capability_code=step.capability_code,
                            success=True,
                            human_readable_text=result.summary_text,
                            structured_result=result.structured_result,
                            raw_data={"raw_sql": result.raw_sql},
                        )
                    )
                else:
                    step_results.append(
                        CapabilityExecutionResult(
                            step_no=step.step_no,
                            capability_code=step.capability_code,
                            success=False,
                            error=result.error,
                            raw_data={"raw_sql": result.raw_sql} if result.raw_sql else {},
                        )
                    )
                continue

            if step.capability_code == "content.generate":
                text = self._generate_content_text(str(payload.get("text", "")), latest_structured)
                step_results.append(
                    CapabilityExecutionResult(
                        step_no=step.step_no,
                        capability_code=step.capability_code,
                        success=True,
                        human_readable_text=text,
                        structured_result={"content": text},
                        raw_data={"source": "template"},
                    )
                )
                continue

            step_results.append(
                CapabilityExecutionResult(
                    step_no=step.step_no,
                    capability_code=step.capability_code,
                    success=False,
                    error=f"capability not implemented: {step.capability_code}",
                )
            )

        return PlanExecutionResult(
            plan_id=plan.plan_id,
            intent=plan.intent,
            step_results=step_results,
        )

    def run(self, message: str) -> PlanExecutionResult:
        plan = self.plan(message)
        return self.execute(plan)

    def _generate_content_text(self, question: str, structured: dict[str, Any]) -> str:
        if not structured:
            return f"基于你的需求，我先给出说明草稿：{question}。"

        if "top_item" in structured and "value" in structured:
            return (
                f"根据分析结果，{structured['top_item']}为关键关注对象，"
                f"当前数值为{structured['value']}。建议围绕该对象进一步拆解原因与改进动作。"
            )

        if "difference" in structured and "ratio_percent" in structured:
            return (
                f"本期较上期变化{structured['difference']}，环比{structured['ratio_percent']}%。"
                "建议结合业务活动与成本结构进一步归因。"
            )

        if "value" in structured:
            return f"当前查询结果为{structured['value']}。建议结合历史区间继续观察趋势。"

        return f"已完成数据分析，结构化结果如下：{structured}"
