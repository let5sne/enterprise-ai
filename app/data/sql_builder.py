from datetime import date

from app.schemas.data import DataQueryIntent


class SQLBuilder:
    def build(
        self,
        intent: DataQueryIntent,
        metric_info: dict[str, str],
        dimension_info: dict[str, str] | None,
        time_range: str | None,
    ) -> str:
        where_clause = self._build_time_filter(time_range)

        if intent.analysis_type == "ranking":
            if not dimension_info:
                return ""
            direction = "DESC"
            if "最低" in intent.original_question:
                direction = "ASC"

            return (
                "SELECT "
                f"{dimension_info['field']} AS dimension_name, "
                f"SUM({metric_info['field']}) AS metric_value "
                f"FROM {metric_info['table']} "
                f"WHERE {where_clause} "
                f"GROUP BY {dimension_info['field']} "
                f"ORDER BY metric_value {direction} "
                "LIMIT 1"
            )

        if intent.analysis_type == "comparison":
            return (
                "SELECT month, "
                f"SUM({metric_info['field']}) AS metric_value "
                f"FROM {metric_info['table']} "
                f"WHERE {where_clause} "
                "GROUP BY month "
                "ORDER BY month DESC "
                "LIMIT 2"
            )

        if intent.analysis_type == "metric":
            return (
                "SELECT "
                f"SUM({metric_info['field']}) AS metric_value "
                f"FROM {metric_info['table']} "
                f"WHERE {where_clause}"
            )

        return ""

    def _build_time_filter(self, time_range: str | None) -> str:
        today = date.today()
        current_month = today.strftime("%Y-%m")
        if today.month == 1:
            last_month = f"{today.year - 1}-12"
        else:
            last_month = f"{today.year}-{today.month - 1:02d}"

        quarter = ((today.month - 1) // 3) + 1
        current_quarter = f"{today.year}Q{quarter}"
        current_year = str(today.year)

        mapping = {
            "last_month": f"month = '{last_month}'",
            "current_month": f"month = '{current_month}'",
            "current_quarter": f"quarter = '{current_quarter}'",
            "current_year": f"year = '{current_year}'",
        }
        return mapping.get(time_range, "1=1")
