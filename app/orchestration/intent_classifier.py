class IntentClassifier:
    def classify(self, features: dict[str, object]) -> str:
        has_data = bool(features.get("has_data"))
        has_generate = bool(features.get("has_generate"))
        has_knowledge = bool(features.get("has_knowledge"))

        # When both data and knowledge features present, strongly prefer data
        # to avoid false positives from queries like "根据用户要求生成报告"
        # which should be content_only, not knowledge_plus_content
        if has_data and has_knowledge and has_generate:
            # In this case, treat as data_plus_content, not knowledge_plus_content
            return "data_plus_content"

        if has_data and has_knowledge:
            # When both match but no generate signal, ignore knowledge
            has_knowledge = False

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
