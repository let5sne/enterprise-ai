class TaskDecomposer:
    def single_step(self, intent: str, message: str) -> dict[str, str]:
        return {"intent": intent, "message": message}

    def multi_steps(self, intent: str, message: str) -> list[dict[str, str]]:
        if intent == "data_plus_content":
            return [
                {"type": "data", "message": message},
                {"type": "content", "message": message},
            ]
        raise ValueError(f"intent '{intent}' is not a supported multi-step intent")
