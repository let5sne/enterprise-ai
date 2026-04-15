from app.content import ContentService


def test_content_service_generate_from_structured_upstream() -> None:
    service = ContentService()

    text, structured = service.generate(
        instruction="写一段说明",
        source_data={"top_item": "市场部", "value": 98000},
    )

    assert "市场部" in text
    assert "98000" in text
    assert structured["content"] == text


def test_content_service_generate_fallback() -> None:
    service = ContentService()

    text, structured = service.generate(instruction="请给我一段说明", source_data={})

    assert "请给我一段说明" in text
    assert structured["content"] == text
