"""
Shared pytest fixtures for enterprise-ai backend tests.
"""
import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.db import Base, get_db
from main import app

TEST_DATABASE_URL = "sqlite:///./test_enterprise_ai.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    from app.models import knowledge, data, content, process  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """Truncate all tables between tests."""
    yield
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            orchestration_service = getattr(app.state, "orchestration_service", None)
            if orchestration_service is not None:
                orchestration_service.context_store.clear()
            yield c
    finally:
        orchestration_service = getattr(app.state, "orchestration_service", None)
        if orchestration_service is not None:
            orchestration_service.context_store.clear()
        app.dependency_overrides.clear()


# -------- LLM / Embedding test doubles --------

class FakeLLMClient:
    """Test double implementing the LLMClient protocol.

    Records calls for assertions and returns a fixed response (or per-call
    callable for dynamic behavior).
    """

    def __init__(self, response: str | None = "FAKE_LLM_OUTPUT") -> None:
        self.response = response
        self.calls: list[dict] = []

    def complete(self, prompt: str, system: str | None = None, **opts) -> str:
        self.calls.append({"prompt": prompt, "system": system, "opts": opts})
        if callable(self.response):
            return self.response(prompt=prompt, system=system, **opts)
        return self.response or ""


class FakeEmbeddingClient:
    """Deterministic hash-based embedding — no network, no model download."""

    def __init__(self, dim: int = 16) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            h = hashlib.sha256((text or "").encode("utf-8")).digest()
            vec = [h[i % len(h)] / 255.0 for i in range(self.dim)]
            out.append(vec)
        return out


@pytest.fixture
def fake_llm_client():
    return FakeLLMClient()


@pytest.fixture
def fake_embedding_client():
    return FakeEmbeddingClient()
