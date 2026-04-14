from app.schemas.context import TaskContext


class FollowupResolver:
    FOLLOWUP_PATTERNS = (
        "继续",
        "再正式一点",
        "更正式一点",
        "再简短一点",
        "更简短一点",
        "再写一版",
        "换个更口语化的版本",
        "改成发给领导的版本",
        "帮我润色一下",
        "再优化一下",
    )

    def is_followup(self, message: str) -> bool:
        msg = message.strip()
        return any(pattern in msg for pattern in self.FOLLOWUP_PATTERNS)

    def can_resume(self, task_context: TaskContext | None) -> bool:
        if not task_context or not task_context.important_outputs:
            return False
        latest_summary = str(task_context.important_outputs.get("latest_summary_text", "") or "")
        return bool(latest_summary.strip())

    def should_resume(self, message: str, task_context: TaskContext | None) -> bool:
        return self.is_followup(message) and self.can_resume(task_context)