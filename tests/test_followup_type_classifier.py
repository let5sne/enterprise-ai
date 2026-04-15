from app.orchestration.followup_type_classifier import FollowupTypeClassifier
from app.orchestration.followup_types import FollowupType
from app.schemas.context import TaskContext


def _task_context(output_type: str) -> TaskContext:
    return TaskContext(
        session_id="sess_classifier",
        important_outputs={
            "latest_output_type": output_type,
            "latest_summary_text": "已有结果",
            "followup_ready": True,
        },
    )


def test_classify_content_refine_from_content() -> None:
    classifier = FollowupTypeClassifier()

    result = classifier.classify("再正式一点", _task_context("content"))

    assert result == FollowupType.CONTENT_REFINE


def test_classify_content_from_previous_data() -> None:
    classifier = FollowupTypeClassifier()

    result = classifier.classify("改成发给领导的版本", _task_context("data"))

    assert result == FollowupType.CONTENT_FROM_PREVIOUS_DATA


def test_classify_content_from_previous_knowledge() -> None:
    classifier = FollowupTypeClassifier()

    result = classifier.classify("写成给员工看的解释", _task_context("knowledge"))

    assert result == FollowupType.CONTENT_FROM_PREVIOUS_KNOWLEDGE


def test_classify_data_continue() -> None:
    classifier = FollowupTypeClassifier()

    result = classifier.classify("换成同比", _task_context("data"))

    assert result == FollowupType.DATA_CONTINUE


def test_classify_knowledge_continue() -> None:
    classifier = FollowupTypeClassifier()

    result = classifier.classify("补充审批节点", _task_context("knowledge"))

    assert result == FollowupType.KNOWLEDGE_CONTINUE


def test_classify_unknown_without_context() -> None:
    classifier = FollowupTypeClassifier()

    result = classifier.classify("换成同比", None)

    assert result == FollowupType.UNKNOWN
