from app.schemas.chat import CitationItem


class CitationBuilder:
    def build(self, docs: list[dict]) -> list[CitationItem]:
        citations: list[CitationItem] = []
        for item in docs:
            citations.append(
                CitationItem(
                    # Per-item override when provided (e.g. "vector_doc"),
                    # else default to the original in-memory source type.
                    source_type=item.get("source_type") or "memory_doc",
                    title=item.get("title") or None,
                    locator=item.get("source") or None,
                    snippet=item.get("content") or None,
                )
            )
        return citations
