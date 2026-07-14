from io import BytesIO

from docx import Document
from sqlalchemy.orm import sessionmaker

from backend import models
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


def create_task_owner(db_session) -> int:
    user = models.User(username="task-owner", password_hash="not-used")
    db_session.add(user)
    db_session.commit()
    return user.id


def install_parser_stub(monkeypatch):
    monkeypatch.setattr(
        import_task_service.imports_service,
        "preview_import_from_file_content",
        lambda _text, _images, **_kwargs: (parsed_question(), [], {"chunks": 1, "ai_ms": 1}),
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


def test_import_task_marks_partial_preview_and_rejects_confirmation(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        import_task_service.imports_service,
        "preview_import_from_file_content",
        lambda _text, _images, **_kwargs: (
            parsed_question(),
            ["第 2 部分解析失败: timeout"],
            {"chunks": 3, "completed_chunks": 2, "failed_chunks": 1, "is_complete": False, "ai_ms": 1},
        ),
    )
    task_id = create_task(client, auth_headers)

    response = client.get(f"/imports/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "partial"
    assert data["progress_current"] == 2
    assert data["progress_total"] == 3
    assert "不能确认导入" in data["error_message"]

    confirm = client.post(f"/imports/tasks/{task_id}/confirm", headers=auth_headers, json={"course_name": "不完整题库"})
    assert confirm.status_code == 409
    assert client.get("/questions/", headers=auth_headers).json() == []


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


def test_recover_pending_tasks_requeues_interrupted_parse(db_session, tmp_path):
    source = tmp_path / "recover.docx"
    source.write_bytes(make_docx())
    owner_id = create_task_owner(db_session)
    task = import_task_service.create_task(
        db_session,
        owner_id=owner_id,
        source_filename="recover.docx",
        file_path=str(source),
    )
    task.status = "parsing"
    db_session.commit()

    scheduled: list[str] = []
    factory = sessionmaker(autocommit=False, autoflush=False, bind=db_session.get_bind())
    recovered = import_task_service.recover_pending_tasks(factory, scheduled.append)

    db_session.expire_all()
    restored = db_session.get(models.ImportTask, task.id)
    assert recovered == [task.id]
    assert scheduled == [task.id]
    assert restored.status == "queued"


def test_recover_pending_tasks_marks_missing_file_as_failed(db_session):
    owner_id = create_task_owner(db_session)
    task = import_task_service.create_task(
        db_session,
        owner_id=owner_id,
        source_filename="gone.docx",
        file_path="D:/missing/gone.docx",
    )

    factory = sessionmaker(autocommit=False, autoflush=False, bind=db_session.get_bind())
    recovered = import_task_service.recover_pending_tasks(factory, lambda _task_id: None)

    db_session.expire_all()
    restored = db_session.get(models.ImportTask, task.id)
    assert recovered == []
    assert restored.status == "failed"
    assert "重新上传" in restored.error_message


def test_recover_pending_tasks_reopens_interrupted_confirmation(db_session, tmp_path):
    source = tmp_path / "confirm.docx"
    source.write_bytes(make_docx())
    owner_id = create_task_owner(db_session)
    task = import_task_service.create_task(
        db_session,
        owner_id=owner_id,
        source_filename="confirm.docx",
        file_path=str(source),
    )
    task.status = "importing"
    db_session.commit()

    factory = sessionmaker(autocommit=False, autoflush=False, bind=db_session.get_bind())
    recovered = import_task_service.recover_pending_tasks(factory, lambda _task_id: None)

    db_session.expire_all()
    restored = db_session.get(models.ImportTask, task.id)
    assert recovered == []
    assert restored.status == "ready"
    assert "确认" in restored.error_message


def test_persist_imported_questions_can_join_callers_transaction(db_session):
    owner_id = create_task_owner(db_session)
    bank = models.QuestionBank(owner_id=owner_id, name="事务题库", visibility="private")
    db_session.add(bank)
    db_session.commit()

    imported = import_task_service.imports_service.persist_imported_questions(
        db_session,
        user_id=owner_id,
        course_id=bank.id,
        questions=parsed_question(),
        commit=False,
    )

    assert imported == 1
    assert db_session.query(models.Question).count() == 1
    db_session.rollback()
    assert db_session.query(models.Question).count() == 0


def test_persist_imported_questions_keeps_rule_bound_question_images(db_session):
    owner_id = create_task_owner(db_session)
    bank = models.QuestionBank(owner_id=owner_id, name="image-bank", visibility="private")
    db_session.add(bank)
    db_session.commit()
    question = parsed_question()[0] | {"image_urls": ["data:image/png;base64,aW1hZ2U="]}

    import_task_service.imports_service.persist_imported_questions(
        db_session,
        user_id=owner_id,
        course_id=bank.id,
        questions=[question],
    )

    stored = db_session.query(models.Question).one()
    assert stored.get_image_urls() == ["data:image/png;base64,aW1hZ2U="]
