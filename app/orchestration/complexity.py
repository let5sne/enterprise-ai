class ComplexityEvaluator:
    def is_multi(self, features: dict[str, object], intent: str) -> bool:
        return intent in ["data_plus_content", "knowledge_plus_content"]
