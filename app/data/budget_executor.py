from __future__ import annotations

from collections import defaultdict
from typing import Any

CURRENT_MONTH = "2026-04"
PREVIOUS_MONTH = "2026-03"

BUDGET_DEMO_ROWS: list[dict[str, Any]] = [
    {
        "month": "2026-04",
        "department_name": "市场部",
        "project_name": "春季获客项目",
        "budget_subject": "营销费用",
        "budget_amount": 100000,
        "actual_amount": 128000,
    },
    {
        "month": "2026-04",
        "department_name": "市场部",
        "project_name": "春季获客项目",
        "budget_subject": "差旅费用",
        "budget_amount": 30000,
        "actual_amount": 36000,
    },
    {
        "month": "2026-04",
        "department_name": "运营部",
        "project_name": "仓配优化项目",
        "budget_subject": "外包服务费",
        "budget_amount": 80000,
        "actual_amount": 98000,
    },
    {
        "month": "2026-04",
        "department_name": "运营部",
        "project_name": "仓配优化项目",
        "budget_subject": "物流费用",
        "budget_amount": 120000,
        "actual_amount": 126000,
    },
    {
        "month": "2026-04",
        "department_name": "行政部",
        "project_name": "办公升级项目",
        "budget_subject": "办公费用",
        "budget_amount": 50000,
        "actual_amount": 59000,
    },
    {
        "month": "2026-04",
        "department_name": "研发部",
        "project_name": "AI平台项目",
        "budget_subject": "云资源费用",
        "budget_amount": 160000,
        "actual_amount": 155000,
    },
    {
        "month": "2026-03",
        "department_name": "市场部",
        "project_name": "春季获客项目",
        "budget_subject": "营销费用",
        "budget_amount": 90000,
        "actual_amount": 112000,
    },
    {
        "month": "2026-03",
        "department_name": "运营部",
        "project_name": "仓配优化项目",
        "budget_subject": "物流费用",
        "budget_amount": 110000,
        "actual_amount": 116000,
    },
    {
        "month": "2026-03",
        "department_name": "行政部",
        "project_name": "办公升级项目",
        "budget_subject": "办公费用",
        "budget_amount": 48000,
        "actual_amount": 47000,
    },
    {
        "month": "2026-03",
        "department_name": "研发部",
        "project_name": "AI平台项目",
        "budget_subject": "云资源费用",
        "budget_amount": 150000,
        "actual_amount": 145000,
    },
]

DIMENSION_FIELD_MAP = {
    "department": "department_name",
    "project": "project_name",
    "budget_subject": "budget_subject",
    "month": "month",
}

DIMENSION_LABEL_MAP = {
    "department": "部门",
    "project": "项目",
    "budget_subject": "预算科目",
    "month": "月份",
}

METRIC_LABEL_MAP = {
    "variance_amount": "超预算金额",
    "actual_amount": "实际发生金额",
    "budget_amount": "预算金额",
    "variance_rate": "超预算率",
}


class BudgetDemoExecutor:
    def execute(self, analysis_type: str, dimension: str | None = None) -> dict[str, Any]:
        if analysis_type == "project_overrun_ranking":
            return self._overrun_ranking("project")

        if analysis_type == "subject_breakdown":
            return self._overrun_ranking("budget_subject")

        if analysis_type == "month_comparison":
            return self._month_comparison()

        return self._overrun_ranking(dimension or "department")

    def _overrun_ranking(self, dimension: str) -> dict[str, Any]:
        field = DIMENSION_FIELD_MAP[dimension]
        grouped: dict[str, dict[str, Any]] = {}
        for row in self._rows_for_month(CURRENT_MONTH):
            item = grouped.setdefault(
                str(row[field]),
                {
                    "dimension_name": row[field],
                    "budget_amount": 0,
                    "actual_amount": 0,
                },
            )
            item["budget_amount"] += row["budget_amount"]
            item["actual_amount"] += row["actual_amount"]

        rows = [self._with_variance(item) for item in grouped.values()]
        rows = [row for row in rows if row["variance_amount"] > 0]
        rows.sort(key=lambda item: item["variance_amount"], reverse=True)

        return {
            "analysis_type": "subject_breakdown" if dimension == "budget_subject" else (
                "project_overrun_ranking" if dimension == "project" else "budget_overrun_ranking"
            ),
            "rows": rows,
            "meta": self._meta(
                analysis_type="subject_breakdown" if dimension == "budget_subject" else (
                    "project_overrun_ranking"
                    if dimension == "project"
                    else "budget_overrun_ranking"
                ),
                dimension=dimension,
                metric="variance_amount",
            ),
            "raw_sql": self._fake_sql(field),
        }

    def _month_comparison(self) -> dict[str, Any]:
        grouped: defaultdict[str, dict[str, Any]] = defaultdict(
            lambda: {"budget_amount": 0, "actual_amount": 0}
        )
        for row in BUDGET_DEMO_ROWS:
            if row["month"] not in {CURRENT_MONTH, PREVIOUS_MONTH}:
                continue
            grouped[row["month"]]["budget_amount"] += row["budget_amount"]
            grouped[row["month"]]["actual_amount"] += row["actual_amount"]

        rows: list[dict[str, Any]] = []
        for month in sorted(grouped.keys(), reverse=True):
            rows.append(
                self._with_variance(
                    {"dimension_name": month, "month": month, **grouped[month]}
                )
            )

        current = rows[0]["actual_amount"] if rows else 0
        previous = rows[1]["actual_amount"] if len(rows) > 1 else 0
        change_amount = current - previous
        change_rate = 0 if previous == 0 else round(change_amount / previous, 4)

        return {
            "analysis_type": "month_comparison",
            "rows": rows,
            "current_actual_amount": current,
            "previous_actual_amount": previous,
            "change_amount": change_amount,
            "change_rate": change_rate,
            "meta": self._meta(
                analysis_type="month_comparison",
                dimension="month",
                metric="actual_amount",
            ),
            "raw_sql": (
                "SELECT month, SUM(budget_amount) AS budget_amount, "
                "SUM(actual_amount) AS actual_amount, "
                "SUM(actual_amount) - SUM(budget_amount) AS variance_amount "
                "FROM demo_budget_actuals WHERE month IN ('2026-04', '2026-03') "
                "GROUP BY month ORDER BY month DESC"
            ),
        }

    def _rows_for_month(self, month: str) -> list[dict[str, Any]]:
        return [row for row in BUDGET_DEMO_ROWS if row["month"] == month]

    def _with_variance(self, item: dict[str, Any]) -> dict[str, Any]:
        budget_amount = float(item["budget_amount"])
        actual_amount = float(item["actual_amount"])
        variance_amount = actual_amount - budget_amount
        item["budget_amount"] = int(budget_amount)
        item["actual_amount"] = int(actual_amount)
        item["variance_amount"] = int(variance_amount)
        item["variance_rate"] = (
            0 if budget_amount == 0 else round(variance_amount / budget_amount, 4)
        )
        return item

    def _meta(self, analysis_type: str, dimension: str, metric: str) -> dict[str, Any]:
        return {
            "analysis_type": analysis_type,
            "dimension": dimension,
            "dimension_label": DIMENSION_LABEL_MAP[dimension],
            "metric": metric,
            "metric_label": METRIC_LABEL_MAP[metric],
        }

    def _fake_sql(self, dimension_field: str) -> str:
        return (
            f"SELECT {dimension_field} AS dimension_name, "
            "SUM(budget_amount) AS budget_amount, "
            "SUM(actual_amount) AS actual_amount, "
            "SUM(actual_amount) - SUM(budget_amount) AS variance_amount, "
            "(SUM(actual_amount) - SUM(budget_amount)) / SUM(budget_amount) AS variance_rate "
            "FROM demo_budget_actuals WHERE month = '2026-04' "
            f"GROUP BY {dimension_field} HAVING SUM(actual_amount) > SUM(budget_amount) "
            "ORDER BY variance_amount DESC"
        )
