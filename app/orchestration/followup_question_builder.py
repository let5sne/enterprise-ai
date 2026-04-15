class FollowupQuestionBuilder:
    def build(
        self,
        message: str,
        latest_user_message: str,
        latest_summary_text: str,
        domain: str,
    ) -> str:
        normalized_message = (message or "").strip()
        previous_question = (latest_user_message or "").strip()
        previous_summary = (latest_summary_text or "").strip()

        base = previous_question or previous_summary
        if not base:
            return normalized_message

        if domain == "data":
            return self._build_data_question(normalized_message, base)

        if domain == "knowledge":
            return self._build_knowledge_question(normalized_message, base)

        return f"基于刚才的内容“{base}”，请继续处理：{normalized_message}"

    def _build_data_question(self, message: str, base: str) -> str:
        if "同比" in message:
            return f"基于“{base}”，请改用同比分析方式继续处理：{message}"

        if "环比" in message:
            return f"基于“{base}”，请改用环比分析方式继续处理：{message}"

        if "上个月" in message or "本月" in message:
            return f"基于“{base}”，请按“{message}”这个时间条件继续分析。"

        if "最低" in message or "最高" in message:
            return f"基于“{base}”，请按“{message}”这个排序方向继续分析。"

        if "按部门" in message or "按产品" in message or "展开" in message:
            return f"基于“{base}”，请按“{message}”这个维度继续展开分析。"

        return f"基于刚才的数据分析需求“{base}”，请继续按这个要求处理：{message}"

    def _build_knowledge_question(self, message: str, base: str) -> str:
        if "审批节点" in message:
            return f"基于“{base}”，请补充审批节点相关说明。"

        if "谁审批" in message:
            return f"基于“{base}”，请说明由谁审批。"

        if "例外" in message or "例外情况" in message:
            return f"基于“{base}”，请补充例外情况说明。"

        if "展开" in message or "补充" in message:
            return f"基于“{base}”，请进一步展开并补充说明：{message}"

        return f"基于刚才的制度/规则问题“{base}”，请继续补充说明：{message}"
