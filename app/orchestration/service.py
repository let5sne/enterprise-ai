from app.schemas.capability import ExecutionPlan

from .capability_mapper import CapabilityMapper
from .complexity import ComplexityEvaluator
from .decomposer import TaskDecomposer
from .intent_classifier import IntentClassifier
from .plan_builder import PlanBuilder
from .preprocessor import MessagePreprocessor


class OrchestrationService:
    def __init__(self) -> None:
        self.preprocessor = MessagePreprocessor()
        self.intent_classifier = IntentClassifier()
        self.complexity = ComplexityEvaluator()
        self.decomposer = TaskDecomposer()
        self.mapper = CapabilityMapper()
        self.builder = PlanBuilder()

    def plan(self, message: str) -> ExecutionPlan:
        features = self.preprocessor.parse(message)
        intent = self.intent_classifier.classify(features)
        is_multi = self.complexity.is_multi(features, intent)

        if not is_multi:
            step = self.decomposer.single_step(intent, message)
            mapped = self.mapper.map_single(step)
            return self.builder.build(intent, [mapped])

        steps = self.decomposer.multi_steps(intent, message)
        mapped = self.mapper.map_multi(steps)
        return self.builder.build(intent, mapped)
