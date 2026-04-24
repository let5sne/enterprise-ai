from __future__ import annotations

from typing import Any


class BudgetResultSummarizer:
    def summarize(self, structured_result: dict[str, Any]) -> str:
        analysis_type = structured_result.get("analysis_type")
        rows = structured_result.get("rows") or []
        meta = structured_result.get("meta") or {}

        if not rows:
            return "本月未发现超预算项目。"

        if analysis_type == "month_comparison":
            change_amount = structured_result.get("change_amount", 0)
            change_rate = structured_result.get("change_rate", 0)
            direction = "增加" if change_amount >= 0 else "减少"
            return (
                f"本月实际成本较上月{direction}{abs(change_amount):.0f}元，"
                f"环比{abs(change_rate) * 100:.2f}%。"
            )

        top = rows[0]
        dimension_label = meta.get("dimension_label") or "维度"
        metric_label = meta.get("metric_label") or "超预算金额"
        return (
            f"本月共有 {len(rows)} 个{dimension_label}超预算，其中"
            f"{top['dimension_name']}超预算最多，{metric_label}为"
            f"{top['variance_amount']}元，超预算率为{top['variance_rate'] * 100:.2f}%。"
        )
