class KnowledgeRetriever:
    # v1: lightweight in-memory docs for deterministic behavior and tests.
    DOCUMENTS = {
        "expense_process": {
            "title": "报销管理流程",
            "content": "员工提交报销单后，部门负责人初审，财务复核，金额超过阈值需分管负责人审批。",
            "source": "员工手册-财务制度",
        },
        "annual_leave_policy": {
            "title": "年假管理规定",
            "content": "年假按司龄核定，需提前在系统发起申请并完成审批后方可休假。",
            "source": "员工手册-假勤制度",
        },
        "procurement_policy": {
            "title": "采购审批要求",
            "content": "采购需先提交采购申请，按金额区间走部门、财务和管理层审批流程。",
            "source": "采购管理办法",
        },
    }

    KEYWORDS = {
        "expense_process": ("报销", "报销单", "费用"),
        "annual_leave_policy": ("年假", "休假", "请假"),
        "procurement_policy": ("采购", "审批", "请购"),
    }

    def retrieve(self, question: str) -> list[dict[str, str]]:
        q = question.strip()
        matched: list[dict[str, str]] = []

        for key, words in self.KEYWORDS.items():
            if any(word in q for word in words):
                matched.append(self.DOCUMENTS[key])

        if matched:
            return matched

        return [
            {
                "title": "通用制度说明",
                "content": "当前问题未命中专项制度，建议补充关键词（如报销、年假、采购）后重试。",
                "source": "制度知识库-通用指引",
            }
        ]
