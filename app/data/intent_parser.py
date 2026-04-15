from app.schemas.data import DataQueryIntent


class QueryIntentParser:
    def parse(self, question: str) -> DataQueryIntent:
        normalized = question.strip()
        analysis_type = "metric"

        if "最高" in normalized or "最低" in normalized:
            analysis_type = "ranking"
        elif "对比" in normalized or "相比" in normalized or "差" in normalized:
            analysis_type = "comparison"

        return DataQueryIntent(
            original_question=normalized,
            analysis_type=analysis_type,
        )
