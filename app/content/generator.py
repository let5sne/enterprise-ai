class ContentGenerator:
    def generate(self, instruction: str, source_data: dict | None = None) -> str:
        source_data = source_data or {}

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

        return f"基于你的需求，我先给出说明草稿：{instruction}。"
