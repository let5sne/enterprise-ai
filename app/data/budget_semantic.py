from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetAnalysisIntent:
    analysis_type: str
    dimension: str
    metric: str = "variance_amount"


class BudgetSemanticParser:
    BUDGET_KEYWORDS = ("预算", "超预算", "业财", "经营分析", "预算科目")

    def parse(self, question: str) -> BudgetAnalysisIntent | None:
        normalized = question.strip()
        if not self._looks_like_budget_question(normalized):
            return None

        if "科目" in normalized:
            return BudgetAnalysisIntent(
                analysis_type="subject_breakdown",
                dimension="budget_subject",
            )

        if "项目" in normalized:
            return BudgetAnalysisIntent(
                analysis_type="project_overrun_ranking",
                dimension="project",
            )

        if (
            ("上月" in normalized or "上个月" in normalized)
            and ("相比" in normalized or "对比" in normalized or "变化" in normalized)
        ):
            return BudgetAnalysisIntent(
                analysis_type="month_comparison",
                dimension="month",
                metric="actual_amount",
            )

        if "部门" in normalized or "哪些" in normalized or "超预算" in normalized:
            return BudgetAnalysisIntent(
                analysis_type="budget_overrun_ranking",
                dimension="department",
            )

        return BudgetAnalysisIntent(
            analysis_type="budget_overrun_ranking",
            dimension="department",
        )

    def _looks_like_budget_question(self, question: str) -> bool:
        if any(keyword in question for keyword in self.BUDGET_KEYWORDS):
            return True
        return "本月成本" in question and (
            "上月" in question or "上个月" in question or "变化" in question
        )
