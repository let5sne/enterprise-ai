from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Enterprise AI Backend"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./enterprise_ai.db"
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
