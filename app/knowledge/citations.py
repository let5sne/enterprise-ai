from app.schemas.chat import CitationItem


class CitationBuilder:
    def build(self, docs: list[dict[str, str]]) -> list[CitationItem]:
        citations: list[CitationItem] = []
        for item in docs:
            citations.append(
                CitationItem(
                    source_type="memory_doc",
                    title=item.get("title") or None,
                    locator=item.get("source") or None,
                    snippet=item.get("content") or None,
                )
            )
        return citations
