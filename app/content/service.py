from .generator import ContentGenerator


class ContentService:
    def __init__(self) -> None:
        self.generator = ContentGenerator()

    def generate(
        self, instruction: str, source_data: dict | None = None
    ) -> tuple[str, dict[str, str]]:
        source_data = source_data or {}
        text = self.generator.generate(instruction=instruction, source_data=source_data)
        return text, {"content": text}
