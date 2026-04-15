class SemanticLayer:
    METRICS = {
        "成本": {"code": "cost_total", "table": "department_costs", "field": "cost_amount"},
        "销售额": {"code": "sales_total", "table": "department_sales", "field": "sales_amount"},
        "库存": {"code": "inventory_qty", "table": "inventory_status", "field": "qty"},
    }

    DIMENSIONS = {
        "部门": {"code": "department", "field": "department_name"},
        "产品": {"code": "product", "field": "product_name"},
        "月份": {"code": "month", "field": "month"},
    }

    def resolve_metric(self, question: str) -> dict[str, str] | None:
        for key, value in self.METRICS.items():
            if key in question:
                return value
        return None

    def resolve_dimension(self, question: str) -> dict[str, str] | None:
        for key, value in self.DIMENSIONS.items():
            if key in question:
                return value
        return None

    def resolve_time_range(self, question: str) -> str | None:
        if "上个月" in question:
            return "last_month"
        if "本月" in question:
            return "current_month"
        if "本季度" in question:
            return "current_quarter"
        if "今年" in question:
            return "current_year"
        return None
