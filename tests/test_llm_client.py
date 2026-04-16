"""Unit tests for OllamaClient request/response format.

Uses httpx.MockTransport — no real Ollama server needed.
"""
from __future__ import annotations

import httpx
import pytest

from app.llm.client import NullLLMClient, OllamaClient


def test_null_llm_client_raises() -> None:
    client = NullLLMClient()
    with pytest.raises(RuntimeError):
        client.complete("hi")


def test_ollama_client_builds_chat_request_and_parses_response(monkeypatch) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["json"] = _parse_json(request)
        return httpx.Response(
            200,
            json={
                "message": {"role": "assistant", "content": "  hello world  "},
                "done": True,
            },
        )

    transport = httpx.MockTransport(handler)

    # Patch httpx.Client to install our transport.
    original_client = httpx.Client

    def patched_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", patched_client)

    client = OllamaClient(base_url="http://fake:11434", model="test-model")
    out = client.complete("你好", system="be brief", temperature=0.5)

    assert out == "hello world"  # stripped
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/api/chat")
    body = captured["json"]
    assert body["model"] == "test-model"
    assert body["stream"] is False
    assert body["options"]["temperature"] == 0.5
    assert body["messages"] == [
        {"role": "system", "content": "be brief"},
        {"role": "user", "content": "你好"},
    ]


def test_ollama_client_without_system(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "ok"}})

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda *a, **kw: original_client(*a, **{**kw, "transport": transport}),
    )

    client = OllamaClient(base_url="http://fake", model="m")
    assert client.complete("hi") == "ok"


def _parse_json(request: httpx.Request) -> dict:
    import json

    return json.loads(request.content.decode("utf-8"))
