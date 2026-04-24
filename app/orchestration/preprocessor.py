import re


class MessagePreprocessor:
    GENERATE_PATTERN = re.compile(r"写|生成|创建|产出")
    DATA_PATTERN = re.compile(r"多少|最高|最多|分析|成本|统计|对比|预算|超预算|业财|科目|相比|变化")
    # Knowledge pattern: matches institutional/procedural terms
    # 制度, 流程, 规定, 规范: core knowledge words
    # 审批 with context: 审批制度|审批流程|审批要求 all indicate authority/policy
    KNOWLEDGE_PATTERN = re.compile(r"制度|流程|规定|规范|审批(制度|流程|要求|规定|规范|指南)?")

    def parse(self, message: str) -> dict[str, object]:
        msg = message.strip()

        return {
            "text": msg,
            "has_generate": bool(self.GENERATE_PATTERN.search(msg)),
            "has_data": bool(self.DATA_PATTERN.search(msg)),
            "has_knowledge": bool(self.KNOWLEDGE_PATTERN.search(msg)),
        }
