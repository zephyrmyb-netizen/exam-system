"""Regression coverage for resilient long-document AI imports."""

import pytest
from fastapi import HTTPException

from backend.imports.image_extractor import ImagePayload


def _question(text: str) -> dict:
    return {
        "type": "fill_blank",
        "question": text,
        "answer": "答案",
        "analysis": "解析",
    }


def test_chunk_document_text_splits_one_large_numbered_paragraph(monkeypatch):
    """A Word document can store many numbered questions in one paragraph."""
    from backend.imports import import_orchestrator

    monkeypatch.setattr(import_orchestrator, "AI_CHUNK_SIZE", 80)
    text = " ".join(
        f"{index}. 这是第 {index} 道很长的模拟题，包含足够多的文字以触发分块。答案：答案。"
        for index in range(1, 7)
    )

    chunks, _ = import_orchestrator.chunk_document_text(text)

    assert len(chunks) >= 3
    assert all(len(chunk) <= 120 for chunk in chunks)
    assert "1." in chunks[0]
    assert "6." in chunks[-1]


def test_chunk_document_text_caps_short_numbered_questions_per_ai_request(monkeypatch):
    """Short Word paragraphs must not let one AI request contain dozens of questions."""
    from backend.imports import import_orchestrator

    monkeypatch.setattr(import_orchestrator, "AI_CHUNK_SIZE", 10_000)
    text = "\n".join(f"{index}. Simulated question {index}" for index in range(1, 15))

    chunks, _ = import_orchestrator.chunk_document_text(text)

    assert len(chunks) == 3
    assert all(import_orchestrator.count_numbered_question_blocks(chunk) <= 6 for chunk in chunks)
    assert "1." in chunks[0]
    assert "14." in chunks[-1]


def test_incomplete_numbered_chunk_is_retried_in_smaller_batches(monkeypatch):
    """A partial JSON response must be retried instead of silently importing a subset."""
    from backend.imports import import_orchestrator

    text = "\n".join(f"{index}. Simulated question {index}" for index in range(1, 7))
    calls: list[int] = []

    def fake_parse(chunk: str, _index: int, expected_question_count: int = 0):
        calls.append(expected_question_count)
        numbers = [int(match.group(1)) for match in __import__("re").finditer(r"(?m)^(\d+)\.", chunk)]
        if expected_question_count == 6:
            return [_question("question 1")], []
        return [_question(f"question {number}") for number in numbers], []

    monkeypatch.setattr(import_orchestrator, "call_ai_parse_chunk", fake_parse)

    items, warnings = import_orchestrator.parse_chunk_with_coverage_retry(text, 0)

    assert [item["question"] for item in items] == [f"question {index}" for index in range(1, 7)]
    assert calls == [6, 2, 2, 2]
    assert any("自动拆分重试" in warning for warning in warnings)


def test_numbered_document_over_chunk_limit_is_not_silently_imported(monkeypatch):
    """A configured safety limit must fail clearly instead of importing only the first pages."""
    from backend.imports import import_orchestrator

    monkeypatch.setattr(import_orchestrator, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(import_orchestrator, "MAX_CHUNKS", 1)
    text = "\n".join(f"{index}. Simulated question {index}" for index in range(1, 13))

    def fake_parse(chunk: str, _index: int, expected_question_count: int = 0):
        return [_question(f"question {index}") for index in range(1, expected_question_count + 1)], []

    monkeypatch.setattr(import_orchestrator, "call_ai_parse_chunk", fake_parse)

    with pytest.raises(HTTPException) as exc_info:
        import_orchestrator.call_ai_parse(text)

    assert exc_info.value.status_code == 422
    assert "超过安全处理上限" in exc_info.value.detail


def test_file_content_combines_chunked_text_and_image_questions(monkeypatch):
    """Embedded images must not make a long text document skip text parsing."""
    from backend.imports import import_orchestrator

    text_questions = [_question("文本题一"), _question("文本题二")]
    image_questions = [_question("图片题一")]
    monkeypatch.setattr(
        import_orchestrator,
        "call_ai_parse",
        lambda _text: (text_questions, ["文本解析提示"], {"chunks": 2, "ai_ms": 20, "ai_chunks": [10, 10]}),
    )
    monkeypatch.setattr(
        import_orchestrator,
        "call_ai_parse_multimodal",
        lambda _text, _images: (image_questions, ["图片解析提示"], {"chunks": 1, "ai_ms": 10, "ai_chunks": [10]}),
    )

    questions, warnings, timing = import_orchestrator.preview_import_from_file_content(
        "1. 文本题一\n2. 文本题二",
        [ImagePayload(data=b"image", mime_type="image/png", source="题图")],
    )

    assert [item["question"] for item in questions] == ["文本题一", "文本题二", "图片题一"]
    assert warnings == ["文本解析提示", "图片解析提示"]
    assert timing["chunks"] == 3
