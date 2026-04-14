from typing import Any

from app.schemas.capability import CapabilityExecutionResult, PlanStep


class ContentGenerateHandler:
    capability_code = "content.generate"

    def execute(self, step: PlanStep, payload: dict[str, Any]) -> CapabilityExecutionResult:
        text = str(payload.get("text", ""))
        upstream = payload.get("upstream") or {}

        if "top_item" in upstream and "value" in upstream:
            content = (
                f"根据分析结果，{upstream['top_item']}为关键关注对象，"
                f"当前数值为{upstream['value']}。建议围绕该对象进一步拆解原因与改进动作。"
            )
        elif "difference" in upstream and "ratio_percent" in upstream:
            content = (
                f"本期较上期变化{upstream['difference']}，环比{upstream['ratio_percent']}%。"
                "建议结合业务活动与成本结构进一步归因。"
            )
        elif "value" in upstream:
            content = f"当前查询结果为{upstream['value']}。建议结合历史区间继续观察趋势。"
        else:
            content = f"基于你的需求，我先给出说明草稿：{text}。"

        return CapabilityExecutionResult(
            step_no=step.step_no,
            capability_code=step.capability_code,
            success=True,
            human_readable_text=content,
            structured_result={"content": content},
            raw_data={"source": "template"},
        )
