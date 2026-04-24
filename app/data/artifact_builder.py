from __future__ import annotations

from typing import Any

from app.schemas.chat import ArtifactItem


class DataArtifactBuilder:
    def build(self, structured_result: dict[str, Any]) -> list[ArtifactItem]:
        if not structured_result:
            return []

        if self._is_budget_result(structured_result):
            return self._build_budget_artifacts(structured_result)

        return self._build_generic_artifacts(structured_result)

    def _build_budget_artifacts(self, structured_result: dict[str, Any]) -> list[ArtifactItem]:
        rows = structured_result.get("rows") or []
        meta = structured_result.get("meta") or {}
        if not rows:
            return []

        artifacts = [
            ArtifactItem(
                artifact_type="table",
                name="budget_analysis_result",
                title=self._budget_table_title(meta),
                content=rows,
                metadata={
                    "analysis_type": meta.get("analysis_type"),
                    "dimension_label": meta.get("dimension_label"),
                    "metric_label": meta.get("metric_label"),
                },
            )
        ]

        chart = self._build_budget_chart(rows, meta)
        if chart:
            artifacts.append(chart)
        return artifacts

    def _build_generic_artifacts(self, structured_result: dict[str, Any]) -> list[ArtifactItem]:
        artifacts: list[ArtifactItem] = []
        rows = structured_result.get("rows")
        meta = structured_result.get("meta") or {}
        metric_label = meta.get("metric_label")
        dimension_label = meta.get("dimension_label")
        analysis_type = meta.get("analysis_type")

        table_content: list[dict[str, Any]] | None = None
        if rows and isinstance(rows, list):
            table_content = rows
        else:
            flat = {
                k: v
                for k, v in structured_result.items()
                if k not in {"rows", "meta"} and not isinstance(v, (dict, list))
            }
            if flat:
                table_content = [flat]

        if table_content:
            artifacts.append(
                ArtifactItem(
                    artifact_type="table",
                    name="analysis_result",
                    title=self._generic_title(dimension_label, metric_label, analysis_type),
                    content=table_content,
                    metadata={
                        "analysis_type": analysis_type,
                        "dimension_label": dimension_label,
                        "metric_label": metric_label,
                    },
                )
            )

        chart = self._build_generic_chart(rows, dimension_label, metric_label, analysis_type)
        if chart:
            artifacts.append(chart)
        return artifacts

    def _build_budget_chart(
        self, rows: list[dict[str, Any]], meta: dict[str, Any]
    ) -> ArtifactItem | None:
        metric = meta.get("metric") or "variance_amount"
        metric_label = meta.get("metric_label") or "超预算金额"
        dimension_label = meta.get("dimension_label") or "维度"
        values = [row.get(metric) for row in rows]
        if all(value is None for value in values):
            values = [row.get("variance_amount") for row in rows]
            metric_label = "超预算金额"

        return ArtifactItem(
            artifact_type="chart",
            name="budget_analysis_chart",
            title=self._budget_chart_title(meta),
            content={
                "categories": [str(row.get("dimension_name", "")) for row in rows],
                "series": [{"name": metric_label, "data": values}],
            },
            metadata={
                "chart_type": "bar",
                "x_label": dimension_label,
                "y_label": metric_label,
                "analysis_type": meta.get("analysis_type"),
            },
        )

    def _build_generic_chart(
        self,
        rows: list[dict[str, Any]] | None,
        dimension_label: str | None,
        metric_label: str | None,
        analysis_type: str | None,
    ) -> ArtifactItem | None:
        if not rows or not isinstance(rows, list):
            return None
        category_key = self._find_category_key(rows)
        if not category_key:
            return None

        categories = [str(row.get(category_key, "")) for row in rows]
        values = [row.get("metric_value") for row in rows]
        if not categories or all(v is None for v in values):
            return None

        return ArtifactItem(
            artifact_type="chart",
            name="analysis_chart",
            title=(
                metric_label
                and dimension_label
                and f"各{dimension_label}{metric_label}"
                or metric_label
            ),
            content={
                "categories": categories,
                "series": [{"name": metric_label or "metric_value", "data": values}],
            },
            metadata={
                "chart_type": "bar",
                "x_label": dimension_label or category_key,
                "y_label": metric_label or "metric_value",
                "analysis_type": analysis_type,
            },
        )

    def _find_category_key(self, rows: list[dict[str, Any]]) -> str | None:
        for row in rows:
            for key in row.keys():
                if key != "metric_value":
                    return key
        return None

    def _is_budget_result(self, structured_result: dict[str, Any]) -> bool:
        meta = structured_result.get("meta") or {}
        analysis_type = str(
            meta.get("analysis_type") or structured_result.get("analysis_type") or ""
        )
        return analysis_type in {
            "budget_overrun_ranking",
            "project_overrun_ranking",
            "month_comparison",
            "subject_breakdown",
        }

    def _budget_table_title(self, meta: dict[str, Any]) -> str:
        analysis_type = meta.get("analysis_type")
        if analysis_type == "month_comparison":
            return "本月与上月成本对比"
        if analysis_type == "subject_breakdown":
            return "本月预算科目超预算分析"
        return f"本月{meta.get('dimension_label', '维度')}超预算排名"

    def _budget_chart_title(self, meta: dict[str, Any]) -> str:
        if meta.get("analysis_type") == "month_comparison":
            return "本月与上月实际成本对比"
        return f"本月{meta.get('dimension_label', '维度')}{meta.get('metric_label', '超预算金额')}"

    def _generic_title(
        self,
        dimension_label: str | None,
        metric_label: str | None,
        analysis_type: str | None,
    ) -> str | None:
        if dimension_label and metric_label and analysis_type == "ranking":
            return f"各{dimension_label}{metric_label}排名"
        if metric_label and analysis_type == "comparison":
            return f"{metric_label}同比 / 环比"
        return None
