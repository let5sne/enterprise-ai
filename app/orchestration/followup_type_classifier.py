from app.schemas.context import TaskContext

from .followup_types import FollowupType


class FollowupTypeClassifier:
    CONTENT_STYLE_KEYWORDS = (
        "正式",
        "简短",
        "口语",
        "润色",
        "优化",
        "领导",
        "员工",
        "通知",
        "再写一版",
    )
    CONTENT_TRANSFORM_KEYWORDS = (
        "写成",
        "整理成",
        "改成",
        "转成",
        "说明",
        "解释",
        "摘要",
        "汇报",
    )
    DATA_CONTINUE_KEYWORDS = (
        "同比",
        "环比",
        "上个月",
        "本月",
        "最低",
        "最高",
        "趋势",
        "按部门",
        "按产品",
        "展开",
    )
    KNOWLEDGE_CONTINUE_KEYWORDS = (
        "审批节点",
        "例外",
        "谁审批",
        "什么条件",
        "再展开",
        "还有哪些",
        "补充",
    )
    AMBIGUOUS_SHORT_FOLLOWUP = ("继续", "再来一个", "换一下")

    def classify(self, message: str, task_context: TaskContext | None) -> str:
        normalized = message.strip()
        output_type = self._get_output_type(task_context)

        has_content_style = self._contains_any(normalized, self.CONTENT_STYLE_KEYWORDS)
        has_content_transform = self._contains_any(normalized, self.CONTENT_TRANSFORM_KEYWORDS)
        has_data_continue = self._contains_any(normalized, self.DATA_CONTINUE_KEYWORDS)
        has_knowledge_continue = self._contains_any(normalized, self.KNOWLEDGE_CONTINUE_KEYWORDS)
        is_ambiguous = self._contains_any(normalized, self.AMBIGUOUS_SHORT_FOLLOWUP)

        if output_type == "content":
            if has_content_style or has_content_transform or is_ambiguous:
                return FollowupType.CONTENT_REFINE

        if output_type == "data":
            if has_content_style or has_content_transform:
                return FollowupType.CONTENT_FROM_PREVIOUS_DATA
            if has_data_continue or is_ambiguous:
                return FollowupType.DATA_CONTINUE

        if output_type == "knowledge":
            if has_content_style or has_content_transform:
                return FollowupType.CONTENT_FROM_PREVIOUS_KNOWLEDGE
            if has_knowledge_continue or is_ambiguous:
                return FollowupType.KNOWLEDGE_CONTINUE

        if has_content_style:
            return FollowupType.CONTENT_REFINE

        return FollowupType.UNKNOWN

    def _get_output_type(self, task_context: TaskContext | None) -> str:
        if not task_context:
            return ""
        outputs = task_context.important_outputs or {}
        return str(outputs.get("latest_output_type", "") or "")

    def _contains_any(self, text: str, keywords: tuple[str, ...]) -> bool:
        return any(keyword in text for keyword in keywords)
