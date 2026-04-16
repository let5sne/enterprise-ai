from typing import Any

from app.data import DataService
from app.schemas.capability import CapabilityExecutionResult, PlanStep
from app.schemas.chat import ArtifactItem


class DataAnalyzeHandler:
    capability_code = "data.analyze"

    def __init__(self) -> None:
        self.data_service = DataService()

    def execute(self, step: PlanStep, payload: dict[str, Any]) -> CapabilityExecutionResult:
        try:
            result = self.data_service.analyze(str(payload.get("text", "")))
        except Exception as exc:
            return CapabilityExecutionResult(
                step_no=step.step_no,
                capability_code=step.capability_code,
                success=False,
                error=f"execution error: {exc}",
            )

        if result.success:
            artifacts = self._build_artifacts(result.structured_result)
            return CapabilityExecutionResult(
                step_no=step.step_no,
                capability_code=step.capability_code,
                success=True,
                human_readable_text=result.summary_text,
                structured_result=result.structured_result,
                raw_data={"raw_sql": result.raw_sql},
                artifacts=artifacts,
            )

        return CapabilityExecutionResult(
            step_no=step.step_no,
            capability_code=step.capability_code,
            success=False,
            error=result.error,
            raw_data={"raw_sql": result.raw_sql} if result.raw_sql else {},
        )

    def _build_artifacts(self, structured_result: dict[str, Any]) -> list[ArtifactItem]:
        if not structured_result:
            return []

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
                    title=self._build_title(dimension_label, metric_label, analysis_type),
                    content=table_content,
                    metadata={
                        "analysis_type": analysis_type,
                        "dimension_label": dimension_label,
                        "metric_label": metric_label,
                    },
                )
            )

        chart = self._build_chart(rows, dimension_label, metric_label, analysis_type)
        if chart is not None:
            artifacts.append(chart)

        return artifacts

    @staticmethod
    def _build_title(
        dimension_label: str | None,
        metric_label: str | None,
        analysis_type: str | None,
    ) -> str | None:
        if dimension_label and metric_label and analysis_type == "ranking":
            return f"各{dimension_label}{metric_label}排名"
        if metric_label and analysis_type == "comparison":
            return f"{metric_label}同比 / 环比"
        return None

    @staticmethod
    def _build_chart(
        rows: list[dict[str, Any]] | None,
        dimension_label: str | None,
        metric_label: str | None,
        analysis_type: str | None,
    ) -> ArtifactItem | None:
        if not rows or not isinstance(rows, list):
            return None
        # Identify the category column: first non-metric_value key in any row.
        category_key: str | None = None
        for row in rows:
            for key in row.keys():
                if key != "metric_value":
                    category_key = key
                    break
            if category_key:
                break
        if not category_key:
            return None

        categories = [str(row.get(category_key, "")) for row in rows]
        values = [row.get("metric_value") for row in rows]
        if not categories or all(v is None for v in values):
            return None

        return ArtifactItem(
            artifact_type="chart",
            name="analysis_chart",
            title=metric_label and dimension_label and f"各{dimension_label}{metric_label}" or metric_label,
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
