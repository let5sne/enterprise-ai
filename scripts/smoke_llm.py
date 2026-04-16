"""真机冒烟：对 Ollama + Chroma 打一发真实请求，验证端到端可用。

用法：
    # 前置：ollama serve 已起，qwen2.5:7b / bge-m3 已 pull，索引已构建
    python scripts/smoke_llm.py
    python scripts/smoke_llm.py --skip-knowledge  # 只跑 content

退出码：
    0 = 全绿
    1 = 有任一项失败
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# 允许从项目根运行
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _force_llm_enabled() -> None:
    os.environ.setdefault("LLM_ENABLED", "true")


def _section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def _timed(label: str, fn):
    t0 = time.perf_counter()
    try:
        out = fn()
        dt = (time.perf_counter() - t0) * 1000
        print(f"[OK]   {label}  ({dt:.0f} ms)")
        return out, None
    except Exception as exc:  # noqa: BLE001
        dt = (time.perf_counter() - t0) * 1000
        print(f"[FAIL] {label}  ({dt:.0f} ms)  -> {type(exc).__name__}: {exc}")
        return None, exc


def smoke_content() -> bool:
    from app.content.service import ContentService

    _section("content.generate (LLM 路径)")
    service = ContentService()
    print(f"generator = {type(service.generator).__name__}")

    cases = [
        (
            "structured -> data prompt",
            dict(
                instruction="写一段 200 字的月度经营摘要",
                source_data={"top_item": "市场部", "value": 98000, "unit": "元"},
            ),
        ),
        (
            "refine -> refine prompt",
            dict(
                instruction="再正式一点，加上结论",
                previous_text="市场部本月成本最高，约 9.8 万元。",
            ),
        ),
        (
            "plain -> plain prompt",
            dict(instruction="写一句公司年会开场白"),
        ),
    ]
    ok = True
    for name, kwargs in cases:
        result, err = _timed(name, lambda kw=kwargs: service.generate(**kw))
        if err is not None:
            ok = False
            continue
        text, _structured = result
        preview = text.replace("\n", " ")[:120]
        print(f"       -> {preview}{'…' if len(text) > 120 else ''}")
    return ok


def smoke_knowledge() -> bool:
    from app.knowledge.service import KnowledgeService

    _section("knowledge.ask (RAG 路径)")
    service = KnowledgeService()
    print(f"retriever = {type(service.retriever).__name__}")

    questions = [
        "采购审批的金额区间是怎么划分的？",
        "年假能否跨年使用？",
        "出差报销需要哪些材料？",
    ]
    ok = True
    for q in questions:
        result, err = _timed(f"ask: {q}", lambda qq=q: service.ask(qq))
        if err is not None:
            ok = False
            continue
        answer, structured = result
        citations = structured.get("citations", [])
        preview = answer.replace("\n", " ")[:120]
        print(f"       answer   -> {preview}{'…' if len(answer) > 120 else ''}")
        print(f"       citations-> {len(citations)} 条")
        for c in citations[:2]:
            src_type = getattr(c, "source_type", "?")
            locator = getattr(c, "locator", "?")
            print(f"                   [{src_type}] {locator}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-content", action="store_true")
    parser.add_argument("--skip-knowledge", action="store_true")
    args = parser.parse_args()

    _force_llm_enabled()
    # 重新加载 settings 以吃到 env
    from app.config import settings  # noqa: E402

    print(f"LLM_ENABLED    = {settings.llm_enabled}")
    print(f"LLM_BASE_URL   = {settings.llm_base_url}")
    print(f"LLM_MODEL      = {settings.llm_model}")
    print(f"EMBEDDING_MODEL= {settings.embedding_model}")
    print(f"VECTOR_DB_PATH = {settings.vector_db_path}")

    if not settings.llm_enabled:
        print("\n[WARN] settings.llm_enabled 为 False，请在 .env 中设置 LLM_ENABLED=true 或直接 export。")
        return 1

    results: list[bool] = []
    if not args.skip_content:
        results.append(smoke_content())
    if not args.skip_knowledge:
        results.append(smoke_knowledge())

    _section("SUMMARY")
    if all(results):
        print("全部冒烟通过 ✅")
        return 0
    print("有失败项，请检查上方日志 ❌")
    return 1


if __name__ == "__main__":
    sys.exit(main())
