from app.schemas.data import DataAnalysisResult

from .intent_parser import QueryIntentParser
from .query_executor import QueryExecutor
from .semantic_layer import SemanticLayer
from .sql_builder import SQLBuilder
from .sql_guard import SQLGuard
from .summarizer import ResultSummarizer


class DataService:
    def __init__(self) -> None:
        self.intent_parser = QueryIntentParser()
        self.semantic = SemanticLayer()
        self.sql_builder = SQLBuilder()
        self.sql_guard = SQLGuard()
        self.executor = QueryExecutor()
        self.summarizer = ResultSummarizer()

    def analyze(self, question: str) -> DataAnalysisResult:
        intent = self.intent_parser.parse(question)

        metric_info = self.semantic.resolve_metric(question)
        dimension_info = self.semantic.resolve_dimension(question)
        time_range = self.semantic.resolve_time_range(question)

        if not metric_info:
            return DataAnalysisResult(success=False, error="无法识别查询指标")

        if intent.analysis_type == "ranking" and not dimension_info:
            return DataAnalysisResult(success=False, error="无法识别排名维度")

        allowed_identifiers = {
            metric_info["table"],
            metric_info["field"],
        }
        if dimension_info:
            allowed_identifiers.add(dimension_info["field"])

        sql = self.sql_builder.build(intent, metric_info, dimension_info, time_range)
        if not sql:
            return DataAnalysisResult(success=False, error="无法生成查询语句")

        ok, reason = self.sql_guard.check(sql, allowed_identifiers=allowed_identifiers)
        if not ok:
            return DataAnalysisResult(success=False, error=f"SQL安全校验失败: {reason}", raw_sql=sql)

        rows = self.executor.execute(sql)
        summary_text, structured = self.summarizer.summarize(intent, rows)

        return DataAnalysisResult(
            success=True,
            summary_text=summary_text,
            structured_result=structured,
            raw_sql=sql,
        )
