from typing import Any


class QueryExecutor:
    def execute(self, sql: str) -> list[dict[str, Any]]:
        upper_sql = sql.upper()

        if "ORDER BY METRIC_VALUE DESC" in upper_sql:
            return [{"dimension_name": "市场部", "metric_value": 520000}]

        if "ORDER BY METRIC_VALUE ASC" in upper_sql:
            return [{"dimension_name": "行政部", "metric_value": 160000}]

        if "GROUP BY MONTH" in upper_sql:
            return [
                {"month": "2026-04", "metric_value": 620000},
                {"month": "2026-03", "metric_value": 520000},
            ]

        return [{"metric_value": 520000}]
