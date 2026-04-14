class ComplexityEvaluator:
    def is_multi(self, features: dict[str, object], intent: str) -> bool:
        return intent in ["data_plus_content"] or bool(features.get("has_and"))
