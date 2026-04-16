from typing import Protocol, runtime_checkable

import httpx

from app.config import settings


@runtime_checkable
class EmbeddingClient(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class NullEmbeddingClient:
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError(
            "Embedding client is disabled because LLM_ENABLED=false. "
            "Set LLM_ENABLED=true to use local embedding model."
        )

class OllamaEmbeddingClient:
    """Calls Ollama /api/embeddings per text (Ollama embedding endpoint is single-input)."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.embedding_model
        self.timeout = timeout

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        results: list[list[float]] = []
        with httpx.Client(timeout=self.timeout) as client:
            for text in texts:
                resp = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                resp.raise_for_status()
                data = resp.json()
                results.append(list(data.get("embedding") or []))
        return results


def get_default_embedding_client() -> EmbeddingClient:
    if settings.llm_enabled:
        return OllamaEmbeddingClient()
    return NullEmbeddingClient()
