from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Enterprise AI Backend"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./enterprise_ai.db"
    debug: bool = False
    # Session/task context TTL in seconds. None means no automatic expiration.
    context_ttl_seconds: float | None = None

    # --- Local LLM / RAG (private deployment) ---
    # When False, content.generate uses TemplateContentGenerator and
    # knowledge.ask uses KeywordRetriever — deterministic fallback paths.
    llm_enabled: bool = False
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:7b"
    embedding_model: str = "bge-m3"
    vector_db_path: str = ".chroma"
    knowledge_docs_dir: str = "data/knowledge_docs"
    knowledge_collection: str = "knowledge"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
