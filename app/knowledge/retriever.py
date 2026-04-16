import logging
from typing import Any

logger = logging.getLogger(__name__)


class KeywordRetriever:
    """v1: lightweight in-memory docs — deterministic default path.

    Used when ``LLM_ENABLED=false`` or when the vector backend is unavailable.
    Matches the original behavior exactly so existing tests pass unchanged.
    """

    DOCUMENTS = {
        "expense_process": {
            "title": "报销管理流程",
            "content": "员工提交报销单后，部门负责人初审，财务复核，金额超过阈值需分管负责人审批。",
            "source": "员工手册-财务制度",
        },
        "annual_leave_policy": {
            "title": "年假管理规定",
            "content": "年假按司龄核定，需提前在系统发起申请并完成审批后方可休假。",
            "source": "员工手册-假勤制度",
        },
        "procurement_policy": {
            "title": "采购审批要求",
            "content": "采购需先提交采购申请，按金额区间走部门、财务和管理层审批流程。",
            "source": "采购管理办法",
        },
    }

    KEYWORDS = {
        "expense_process": ("报销", "报销单", "费用"),
        "annual_leave_policy": ("年假", "休假", "请假"),
        "procurement_policy": ("采购", "审批", "请购"),
    }

    def retrieve(self, question: str) -> list[dict[str, str]]:
        q = question.strip()
        matched: list[dict[str, str]] = []

        for key, words in self.KEYWORDS.items():
            if any(word in q for word in words):
                matched.append(self.DOCUMENTS[key])

        if matched:
            return matched

        return [
            {
                "title": "通用制度说明",
                "content": "当前问题未命中专项制度，建议补充关键词（如报销、年假、采购）后重试。",
                "source": "制度知识库-通用指引",
            }
        ]


class VectorRetriever:
    """Chroma-backed semantic retriever. Requires an embedding client and the
    ``chromadb`` package. Lazy imports so tests that don't need it aren't
    affected when chromadb isn't installed.
    """

    def __init__(
        self,
        collection_name: str | None = None,
        persist_path: str | None = None,
        embedding_client: Any = None,
    ) -> None:
        from app.config import settings
        from app.llm.embeddings import get_default_embedding_client

        try:
            import chromadb  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "chromadb is not installed. Run `pip install chromadb` to enable VectorRetriever."
            ) from exc

        self.collection_name = collection_name or settings.knowledge_collection
        self.persist_path = persist_path or settings.vector_db_path
        self.embedding_client = embedding_client or get_default_embedding_client()
        self._chromadb = chromadb
        self._client = chromadb.PersistentClient(path=self.persist_path)
        self._collection = self._client.get_or_create_collection(name=self.collection_name)

    def retrieve(self, question: str, top_k: int = 3) -> list[dict[str, Any]]:
        try:
            embeddings = self.embedding_client.embed([question])
            if not embeddings or not embeddings[0]:
                return []
            results = self._collection.query(
                query_embeddings=embeddings,
                n_results=top_k,
            )
        except Exception as exc:
            logger.warning("VectorRetriever query failed (%s) — returning empty.", exc)
            return []

        ids = (results.get("ids") or [[]])[0]
        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]

        docs: list[dict[str, Any]] = []
        for i, chunk_text in enumerate(documents):
            meta = metadatas[i] if i < len(metadatas) else {}
            dist = distances[i] if i < len(distances) else 0.0
            docs.append(
                {
                    "title": meta.get("title") or meta.get("source_path") or "",
                    "content": chunk_text,
                    "source": meta.get("source_path") or "",
                    "source_type": "vector_doc",
                    "score": max(0.0, 1.0 - float(dist)),
                    "chunk_id": ids[i] if i < len(ids) else "",
                }
            )
        return docs


# Backward-compat alias — older code imports ``KnowledgeRetriever``.
KnowledgeRetriever = KeywordRetriever


__all__ = ["KeywordRetriever", "VectorRetriever", "KnowledgeRetriever"]
