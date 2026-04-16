import logging
from typing import Any

from app.config import settings
from app.llm import prompts as llm_prompts
from app.llm.client import LLMClient, get_default_llm_client
from app.schemas.chat import CitationItem

from .citations import CitationBuilder
from .retriever import KeywordRetriever

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(
        self,
        retriever: Any = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.retriever = retriever or self._build_default_retriever()
        self.citation_builder = CitationBuilder()
        self.llm_client = llm_client

    @staticmethod
    def _build_default_retriever() -> Any:
        if not settings.llm_enabled:
            return KeywordRetriever()

        try:
            from .retriever import VectorRetriever

            return VectorRetriever()
        except Exception as exc:
            logger.warning(
                "VectorRetriever unavailable (%s); degrading to KeywordRetriever.", exc
            )
            return KeywordRetriever()

    def _synthesize_answer(self, question: str, docs: list[dict]) -> str | None:
        if not settings.llm_enabled:
            return None

        if self.llm_client is None:
            try:
                self.llm_client = get_default_llm_client()
            except Exception:  # pragma: no cover
                return None

        context = "\n\n".join(
            f"[{i + 1}] {d.get('title', '')} — {d.get('content', '')}"
            for i, d in enumerate(docs[:5])
        )
        prompt = llm_prompts.KNOWLEDGE_QA_TEMPLATE.format(
            question=question,
            context=context,
        )
        try:
            text = self.llm_client.complete(prompt, system=llm_prompts.KNOWLEDGE_SYSTEM)
            text = (text or "").strip()
            return text or None
        except Exception as exc:
            logger.warning("LLM knowledge synthesis failed (%s) — using template answer.", exc)
            return None

    def ask(self, question: str) -> tuple[str, dict[str, Any]]:
        docs = self.retriever.retrieve(question) or []
        if not docs:
            # Safety net: degrade to keyword retrieval when vector returns nothing.
            docs = KeywordRetriever().retrieve(question)
        
            if not docs:
                answer = "抱歉，暂时未检索到相关制度资料。"
                structured = {"answer": answer, "citations": []}
                return answer, structured

        top_doc = docs[0]
        citations: list[CitationItem] = self.citation_builder.build(docs)

        answer = self._synthesize_answer(question, docs)
        if not answer:
            answer = f"根据制度资料，{top_doc.get('content', '')}"

        structured = {
            "answer": answer,
            "citations": citations,
        }
        return answer, structured
