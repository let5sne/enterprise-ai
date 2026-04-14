from .generator import ContentGenerator


class ContentService:
    def __init__(self) -> None:
        self.generator = ContentGenerator()

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
