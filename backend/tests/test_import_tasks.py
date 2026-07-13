from io import BytesIO

from docx import Document

from backend.services import import_task_service


def make_docx() -> bytes:
    document = Document()
    document.add_paragraph("1. 模块化导入测试题？答案：正确。")
    stream = BytesIO()
    document.save(stream)
    return stream.getvalue()


def parsed_question():
    return [
        {
            "type": "fill_blank",
            "question": "模块化导入测试题？",
            "answer": "正确",
            "analysis": "用于验证后台任务。",
            "subject": "测试",
            "chapter": "第一章",
            "difficulty": "normal",
        }
    ]


def install_parser_stub(monkeypatch):
    monkeypatch.setattr(
        import_task_service.imports_service,
        "preview_import_from_file_content",
        lambda _text, _images: (parsed_question(), [], {"chunks": 1, "ai_ms": 1}),
    )


def create_task(client, auth_headers):
    response = client.post(
        "/imports/tasks",
        headers=auth_headers,
        files={"file": ("module.docx", make_docx(), "application/octet-stream")},
    )
    assert response.status_code == 202
    return response.json()["id"]


def test_import_task_persists_preview_after_background_parse(client, auth_headers, monkeypatch):
    install_parser_stub(monkeypatch)
    task_id = create_task(client, auth_headers)

    response = client.get(f"/imports/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["total_valid"] == 1
    assert data["questions"][0]["question"] == "模块化导入测试题？"


def test_import_task_is_invisible_to_other_users(client, auth_headers, auth_headers_other, monkeypatch):
    install_parser_stub(monkeypatch)
    task_id = create_task(client, auth_headers)

    response = client.get(f"/imports/tasks/{task_id}", headers=auth_headers_other)
    assert response.status_code == 404


def test_import_task_confirm_is_idempotent(client, auth_headers, monkeypatch):
    install_parser_stub(monkeypatch)
    task_id = create_task(client, auth_headers)

    first = client.post(
        f"/imports/tasks/{task_id}/confirm",
        headers=auth_headers,
        json={"course_name": "任务题库"},
    )
    assert first.status_code == 200
    assert first.json()["imported_count"] == 1

    second = client.post(
        f"/imports/tasks/{task_id}/confirm",
        headers=auth_headers,
        json={"course_name": "任务题库"},
    )
    assert second.status_code == 200
    assert second.json()["imported_count"] == 1

    questions = client.get("/questions/", headers=auth_headers).json()
    assert len(questions) == 1
