"""预算助手 Demo 冒烟脚本。

用途：
1. 用固定话术演示预算分析能力
2. 验证多轮 follow-up 是否连贯
3. 输出可直接复盘的关键信息

用法：
    python scripts/smoke_budget_demo.py
    python scripts/smoke_budget_demo.py --session-id sess_demo_001

退出码：
    0 = 全部通过
    1 = 任一步骤失败
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

# 允许从项目根直接运行
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from main import app  # noqa: E402


def _section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def _preview(text: str, limit: int = 120) -> str:
    normalized = text.replace("\n", " ").strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit] + "…"


def _post_case(client: TestClient, payload: dict[str, Any]) -> tuple[dict[str, Any] | None, Exception | None]:
    start = time.perf_counter()
    try:
        response = client.post("/api/v1/chat/ask", json=payload)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.raise_for_status()
        data = response.json()
        print(f"[OK]   {payload['message']}  ({elapsed_ms:.0f} ms)")
        return data, None
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[FAIL] {payload['message']}  ({elapsed_ms:.0f} ms) -> {type(exc).__name__}: {exc}")
        return None, exc


def _assert_budget_result(data: dict[str, Any]) -> None:
    assert data["answer"]
    assert data["debug"]["raw_sql"]

    table = next(item for item in data["artifacts"] if item["artifact_type"] == "table")
    chart = next(item for item in data["artifacts"] if item["artifact_type"] == "chart")

    metadata = table["metadata"]
    assert metadata["analysis_type"]
    assert metadata["dimension_label"]
    assert metadata["metric_label"]
    assert len(chart["content"]["categories"]) == len(chart["content"]["series"][0]["data"])


def _print_summary(data: dict[str, Any]) -> None:
    print(f"       answer      -> {_preview(data['answer'])}")
    print(f"       intent      -> {data['debug']['intent']}")
    print(f"       capabilities-> {', '.join(data['capabilities_used'])}")
    print(f"       raw_sql     -> {bool(data['debug'].get('raw_sql'))}")
    for artifact in data["artifacts"]:
        print(f"       artifact    -> {artifact['artifact_type']} / {artifact['name']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", default="sess_budget_demo_smoke")
    args = parser.parse_args()

    standalone_cases = [
        {"user_id": "u1", "source": "web", "message": "本月哪些部门超预算？"},
        {"user_id": "u1", "source": "web", "message": "哪个项目超预算最多？"},
        {"user_id": "u1", "source": "web", "message": "本月成本和上月相比变化如何？"},
    ]
    followup_cases = [
        {
            "session_id": args.session_id,
            "user_id": "u1",
            "source": "web",
            "message": "本月哪些部门超预算？",
        },
        {
            "session_id": args.session_id,
            "user_id": "u1",
            "source": "web",
            "message": "按预算科目展开一下",
        },
        {
            "session_id": args.session_id,
            "user_id": "u1",
            "source": "web",
            "message": "写成给领导看的经营分析说明",
        },
    ]

    ok = True
    with TestClient(app) as client:
        _section("单轮预算分析")
        for payload in standalone_cases:
            data, err = _post_case(client, payload)
            if err is not None or data is None:
                ok = False
                continue
            try:
                _assert_budget_result(data)
                _print_summary(data)
            except Exception as exc:  # noqa: BLE001
                ok = False
                print(f"[FAIL] 结果校验失败 -> {type(exc).__name__}: {exc}")

        _section("多轮 follow-up")
        first, err = _post_case(client, followup_cases[0])
        if err is not None or first is None:
            ok = False
        else:
            try:
                _assert_budget_result(first)
                _print_summary(first)
            except Exception as exc:  # noqa: BLE001
                ok = False
                print(f"[FAIL] 首轮结果校验失败 -> {type(exc).__name__}: {exc}")

        second, err = _post_case(client, followup_cases[1])
        if err is not None or second is None:
            ok = False
        else:
            try:
                table = next(item for item in second["artifacts"] if item["artifact_type"] == "table")
                assert second["debug"]["intent"] == "data_followup"
                assert second["capabilities_used"] == ["data.analyze"]
                assert table["metadata"]["analysis_type"] == "subject_breakdown"
                _print_summary(second)
            except Exception as exc:  # noqa: BLE001
                ok = False
                print(f"[FAIL] 科目展开校验失败 -> {type(exc).__name__}: {exc}")

        third, err = _post_case(client, followup_cases[2])
        if err is not None or third is None:
            ok = False
        else:
            try:
                text_artifact = next(
                    item for item in third["artifacts"] if item["artifact_type"] == "text"
                )
                assert third["capabilities_used"] == ["content.generate"]
                assert "领导您好" in third["answer"]
                assert text_artifact["content"] == third["answer"]
                _print_summary(third)
            except Exception as exc:  # noqa: BLE001
                ok = False
                print(f"[FAIL] 领导汇报校验失败 -> {type(exc).__name__}: {exc}")

    _section("SUMMARY")
    if ok:
        print("预算助手 Demo 冒烟通过")
        return 0

    print("预算助手 Demo 冒烟失败，请检查上方日志")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
