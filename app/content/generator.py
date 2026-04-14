class ContentGenerator:
    FOLLOWUP_KEYWORDS = (
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

    def generate(
        self,
        instruction: str,
        source_data: dict | None = None,
        previous_text: str | None = None,
    ) -> str:
        source_data = source_data or {}
        previous_text = (previous_text or "").strip()
        normalized = instruction.strip()

        # Prefer refinement against previous output when available.
        if previous_text:
            if "再正式一点" in normalized or "更正式一点" in normalized:
                return f"现将有关情况说明如下：{previous_text}"

            if "再简短一点" in normalized or "更简短一点" in normalized:
                return f"简要说明：{previous_text}"

            if "发给领导" in normalized or "领导" in normalized:
                return f"领导您好，现将有关情况简要汇报如下：{previous_text}"

            if "润色" in normalized or "优化" in normalized:
                return f"经优化后的表述如下：{previous_text}"

            if "再写一版" in normalized:
                return f"现重新表述如下：{previous_text}"

            if "口语化" in normalized:
                return f"下面给你一个更口语化的版本：{previous_text}"

            if "继续" in normalized:
                return previous_text

        if any(keyword in normalized for keyword in self.FOLLOWUP_KEYWORDS):
            return "抱歉，我没有找到可供调整的上一轮输出，请先让我生成一版初稿。"

        if "top_item" in source_data and "value" in source_data:
            return (
                f"根据分析结果，{source_data['top_item']}为关键关注对象，"
                f"当前数值为{source_data['value']}。建议围绕该对象进一步拆解原因与改进动作。"
            )

        if "difference" in source_data and "ratio_percent" in source_data:
            return (
                f"本期较上期变化{source_data['difference']}，环比{source_data['ratio_percent']}%。"
                "建议结合业务活动与成本结构进一步归因。"
            )

        if "value" in source_data:
            return f"当前查询结果为{source_data['value']}。建议结合历史区间继续观察趋势。"

        if "answer" in source_data:
            return f"根据已有资料，建议表述为：{source_data['answer']}"

        return f"基于你的需求，我先给出说明草稿：{instruction}。"
