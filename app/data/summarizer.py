from typing import Any

from app.schemas.data import DataQueryIntent


class ResultSummarizer:
    def summarize(self, intent: DataQueryIntent, rows: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        if not rows:
            return "未查询到符合条件的数据。", {}

        if intent.analysis_type == "ranking":
            top = rows[0]
            text = f"查询结果显示，最高项为{top['dimension_name']}，对应数值为{top['metric_value']}。"
            return text, {"top_item": top["dimension_name"], "value": top["metric_value"]}

        if intent.analysis_type == "comparison":
            if len(rows) < 2:
                value = rows[0].get("metric_value")
                return f"对比样本不足，当前值为 {value}。", {"current_value": value}

            current = float(rows[0].get("metric_value", 0))
            previous = float(rows[1].get("metric_value", 0))
            diff = current - previous
            ratio = 0.0 if previous == 0 else (diff / previous) * 100
            text = f"本期相比上期变化 {diff:.0f}，环比 {ratio:.2f}%。"
            return text, {
                "current": current,
                "previous": previous,
                "difference": diff,
                "ratio_percent": round(ratio, 2),
            }

        value = rows[0].get("metric_value")
        text = f"查询结果为 {value}。"
        return text, {"value": value}
