from app.config import settings
from app.llm.client import get_default_llm_client

from .generator import LLMContentGenerator, TemplateContentGenerator


class ContentService:
    def __init__(self, generator=None) -> None:
        if generator is not None:
            self.generator = generator
        elif settings.llm_enabled:
            self.generator = LLMContentGenerator(llm_client=get_default_llm_client())
        else:
            self.generator = TemplateContentGenerator()

    def generate(
        self,
        instruction: str,
        source_data: dict | None = None,
        previous_text: str | None = None,
    ) -> tuple[str, dict[str, str]]:
        source_data = source_data or {}
        text = self.generator.generate(
            instruction=instruction,
            source_data=source_data,
            previous_text=previous_text,
        )
        return text, {"content": text}
