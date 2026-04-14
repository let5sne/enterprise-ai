from app.schemas.capability import InputBinding, PlanStep


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
            bindings: list[InputBinding] = []
            if code == "content.generate" and i > 0:
                bindings.append(
                    InputBinding(
                        from_step_no=i,
                        from_field="structured_result",
                        to_param="upstream",
                    )
                )
            result.append(
                PlanStep(
                    step_no=i + 1,
                    capability_code=code,
                    input_data={"text": item["message"]},
                    input_bindings=bindings,
                )
            )

        return result
