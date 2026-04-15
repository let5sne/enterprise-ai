from .citations import CitationBuilder
from .retriever import KnowledgeRetriever


class KnowledgeService:
    def __init__(self) -> None:
        self.retriever = KnowledgeRetriever()
        self.citation_builder = CitationBuilder()

    def ask(self, question: str) -> tuple[str, dict[str, object]]:
        docs = self.retriever.retrieve(question)
        top_doc = docs[0]
        citations = self.citation_builder.build(docs)

        answer = f"根据制度资料，{top_doc.get('content', '')}"
        structured = {
            "answer": answer,
            "citations": citations,
        }
        return answer, structured
