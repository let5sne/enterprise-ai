class IntentClassifier:
    def classify(self, features: dict[str, object]) -> str:
        has_data = bool(features.get("has_data"))
        has_generate = bool(features.get("has_generate"))
        has_knowledge = bool(features.get("has_knowledge"))

        if has_data and has_generate:
            return "data_plus_content"

        if has_knowledge and has_generate:
            return "knowledge_plus_content"

        if has_data:
            return "data_only"

        if has_generate:
            return "content_only"

        if has_knowledge:
            return "knowledge_only"

        return "content_only"
