from typing import Any, Protocol, runtime_checkable

import httpx

from app.config import settings


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, prompt: str, system: str | None = None, **opts: Any) -> str: ...


class NullLLMClient:
    """Used when llm_enabled=False. Raises if called — callers must gate by settings."""

    def complete(self, prompt: str, system: str | None = None, **opts: Any) -> str:
        raise RuntimeError(
            "LLM is disabled. Set LLM_ENABLED=true and start a local Ollama server to enable."
        )


class OllamaClient:
    """Minimal Ollama /api/chat client. Blocking; one-shot (no streaming)."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = timeout

    def complete(self, prompt: str, system: str | None = None, **opts: Any) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": float(opts.get("temperature", 0.2)),
            },
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        message = data.get("message") or {}
        return (message.get("content") or "").strip()


def get_default_llm_client() -> LLMClient:
    if settings.llm_enabled:
        return OllamaClient()
    return NullLLMClient()
