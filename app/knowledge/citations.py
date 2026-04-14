class CitationBuilder:
    def build(self, docs: list[dict[str, str]]) -> list[dict[str, str]]:
        citations: list[dict[str, str]] = []
        for item in docs:
            citations.append(
                {
                    "title": item.get("title", ""),
                    "source": item.get("source", ""),
                }
            )
        return citations
