from app.schemas.capability import PlanStep


class CapabilityMapper:
    def map_single(self, step: dict[str, str]) -> PlanStep:
        intent = step["intent"]

        if intent == "knowledge_only":
            code = "knowledge.ask"
        elif intent == "data_only":
            code = "data.analyze"
        elif intent == "content_only":
            code = "content.generate"
        else:
            code = "content.generate"

        return PlanStep(
            step_no=1,
            capability_code=code,
            input_data={"text": step["message"]},
        )

    def map_multi(self, steps: list[dict[str, str]]) -> list[PlanStep]:
        result: list[PlanStep] = []

        for i, item in enumerate(steps):
            code = "data.analyze" if item["type"] == "data" else "content.generate"
            result.append(
                PlanStep(
                    step_no=i + 1,
                    capability_code=code,
                    input_data={"text": item["message"]},
                )
            )

        return result
