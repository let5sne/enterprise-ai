from app.orchestration.followup_question_builder import FollowupQuestionBuilder


def test_build_data_question_for_yoy() -> None:
    builder = FollowupQuestionBuilder()

    result = builder.build(
        message="换成同比",
        latest_user_message="帮我看上个月哪个部门成本最高",
        latest_summary_text="查询结果显示最高项为市场部",
        domain="data",
    )

    assert "同比" in result
    assert "帮我看上个月哪个部门成本最高" in result


def test_build_data_question_for_dimension_expand() -> None:
    builder = FollowupQuestionBuilder()

    result = builder.build(
        message="按部门展开一下",
        latest_user_message="帮我看本月销售额情况",
        latest_summary_text="查询结果为 520000",
        domain="data",
    )

    assert "按部门" in result
    assert "帮我看本月销售额情况" in result


def test_build_knowledge_question_for_approval_nodes() -> None:
    builder = FollowupQuestionBuilder()

    result = builder.build(
        message="补充审批节点",
        latest_user_message="采购审批要求是什么",
        latest_summary_text="采购审批应按金额分级审批",
        domain="knowledge",
    )

    assert "审批节点" in result
    assert "采购审批要求是什么" in result


def test_build_knowledge_question_for_exceptions() -> None:
    builder = FollowupQuestionBuilder()

    result = builder.build(
        message="还有哪些例外情况",
        latest_user_message="年假制度怎么规定",
        latest_summary_text="年假按工龄分档计算",
        domain="knowledge",
    )

    assert "例外" in result or "补充说明" in result
    assert "年假制度怎么规定" in result


def test_build_without_context_returns_original_message() -> None:
    builder = FollowupQuestionBuilder()

    result = builder.build(
        message="换成同比",
        latest_user_message="",
        latest_summary_text="",
        domain="data",
    )

    assert result == "换成同比"


def test_build_data_question_keeps_extra_instruction_on_yoy() -> None:
    builder = FollowupQuestionBuilder()

    result = builder.build(
        message="换成同比，并且按部门展开",
        latest_user_message="帮我看上个月哪个部门成本最高",
        latest_summary_text="查询结果显示最高项为市场部",
        domain="data",
    )

    assert "同比" in result
    assert "按部门展开" in result
