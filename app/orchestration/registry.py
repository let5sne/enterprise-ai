from app.orchestration.handlers.content_generate import ContentGenerateHandler
from app.orchestration.handlers.data_analyze import DataAnalyzeHandler
from app.orchestration.handlers.base import CapabilityHandler
from app.orchestration.handlers.knowledge_ask import KnowledgeAskHandler


class CapabilityRegistry:
    def __init__(self) -> None:
        handlers: list[CapabilityHandler] = [
            DataAnalyzeHandler(),
            ContentGenerateHandler(),
            KnowledgeAskHandler(),
        ]
        self._handlers = {handler.capability_code: handler for handler in handlers}

    def get(self, capability_code: str) -> CapabilityHandler | None:
        return self._handlers.get(capability_code)

    def list_codes(self) -> list[str]:
        return list(self._handlers.keys())
