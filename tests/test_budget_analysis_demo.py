from __future__ import annotations

from typing import Any


def _artifact_by_type(payload: dict[str, Any], artifact_type: str) -> list[dict[str, Any]]:
    return [item for item in payload["artifacts"] if item["artifact_type"] == artifact_type]


def test_budget_department_overrun_demo(client) -> None:
    response = client.post(
        "/api/v1/chat/ask",
        json={"user_id": "u1", "source": "web", "message": "本月哪些部门超预算？"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["debug"]["intent"] == "data_only"
    assert payload["capabilities_used"] == ["data.analyze"]
    assert payload["answer"]
    assert payload["debug"]["raw_sql"]
    assert payload["task_context"]["important_outputs"]["followup_ready"] is True

    tables = _artifact_by_type(payload, "table")
    charts = _artifact_by_type(payload, "chart")
    assert tables and tables[0]["name"] == "budget_analysis_result"
    assert charts and charts[0]["name"] == "budget_analysis_chart"
    assert tables[0]["metadata"]["analysis_type"] == "budget_overrun_ranking"
    assert charts[0]["metadata"]["analysis_type"] == "budget_overrun_ranking"


def test_budget_project_overrun_ranking_demo(client) -> None:
    response = client.post(
        "/api/v1/chat/ask",
        json={"user_id": "u1", "source": "web", "message": "哪个项目超预算最多？"},
    )

    assert response.status_code == 200
    payload = response.json()
    table = _artifact_by_type(payload, "table")[0]
    rows = table["content"]
    assert table["metadata"]["dimension_label"] == "项目"
    assert table["metadata"]["analysis_type"] == "project_overrun_ranking"
    assert rows[0]["dimension_name"] == "春季获客项目"
    assert rows[0]["variance_amount"] == 34000


def test_budget_month_comparison_demo(client) -> None:
    response = client.post(
        "/api/v1/chat/ask",
        json={"user_id": "u1", "source": "web", "message": "本月成本和上月相比变化如何？"},
    )

    assert response.status_code == 200
    payload = response.json()
    chart = _artifact_by_type(payload, "chart")[0]
    content = chart["content"]
    assert chart["metadata"]["analysis_type"] == "month_comparison"
    assert content["categories"] == ["2026-04", "2026-03"]
    assert len(content["categories"]) == len(content["series"][0]["data"])


def test_budget_followup_subject_breakdown_demo(client) -> None:
    session_id = "sess_budget_subject"
    first = client.post(
        "/api/v1/chat/ask",
        json={
            "session_id": session_id,
            "user_id": "u1",
            "source": "web",
            "message": "本月哪些部门超预算？",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/chat/ask",
        json={
            "session_id": session_id,
            "user_id": "u1",
            "source": "web",
            "message": "按预算科目展开一下",
        },
    )

    assert second.status_code == 200
    payload = second.json()
    assert payload["debug"]["intent"] == "data_followup"
    assert payload["capabilities_used"] == ["data.analyze"]
    assert payload["task_context"]["important_outputs"]["latest_capability_code"] == "data.analyze"
    assert payload["task_context"]["important_outputs"]["followup_ready"] is True
    table = _artifact_by_type(payload, "table")[0]
    assert table["metadata"]["analysis_type"] == "subject_breakdown"
    assert table["metadata"]["dimension_label"] == "预算科目"


def test_budget_followup_generate_leadership_summary_demo(client) -> None:
    session_id = "sess_budget_content"
    first = client.post(
        "/api/v1/chat/ask",
        json={
            "session_id": session_id,
            "user_id": "u1",
            "source": "web",
            "message": "本月哪些部门超预算？",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/chat/ask",
        json={
            "session_id": session_id,
            "user_id": "u1",
            "source": "web",
            "message": "写成给领导看的经营分析说明",
        },
    )

    assert second.status_code == 200
    payload = second.json()
    assert payload["capabilities_used"] == ["content.generate"]
    assert "领导您好" in payload["answer"]
    text_artifacts = _artifact_by_type(payload, "text")
    assert text_artifacts
    assert text_artifacts[0]["name"] == "generated_content"
    assert text_artifacts[0]["content"] == payload["answer"]
