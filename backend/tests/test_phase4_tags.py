"""Phase 4 M1 coverage for knowledge tags."""

from backend import models
from backend.repositories.tag_repo import QuestionTagRepository, TagRepository
from backend.services.tag_service import TagService


def _user(db_session, username="alice"):
    user = models.User(username=username, password_hash="hash")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _question(db_session, owner_id, text="What is JVM?"):
    question = models.Question(
        owner_id=owner_id,
        type="short_answer",
        question=text,
        answer="Java Virtual Machine",
        subject="Java",
        chapter="Basics",
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


def test_tag_repository_deduplicates_names_case_insensitively(db_session):
    repo = TagRepository(db_session)

    first = repo.get_or_create(name="Java", color="#2563eb")
    second = repo.get_or_create(name=" java ", color="#ef4444")

    assert first.id == second.id
    assert db_session.query(models.Tag).count() == 1
    assert first.color == "#2563eb"


def test_tag_service_tags_question_once_and_lists_question_tags(db_session):
    user = _user(db_session)
    question = _question(db_session, user.id)
    service = TagService(db_session)

    service.tag_question(question_id=question.id, tag_names=["Java", "OOP", "java"])
    tags = service.list_question_tags(question.id)
    relations = db_session.query(models.QuestionTag).all()

    assert [tag.name for tag in tags] == ["Java", "OOP"]
    assert len(relations) == 2


def test_tag_service_reports_accuracy_by_tag_for_user(db_session):
    user = _user(db_session)
    q1 = _question(db_session, user.id, text="Q1")
    q2 = _question(db_session, user.id, text="Q2")
    service = TagService(db_session)
    service.tag_question(question_id=q1.id, tag_names=["Java"])
    service.tag_question(question_id=q2.id, tag_names=["Java"])
    db_session.add_all(
        [
            models.PracticeRecord(user_id=user.id, question_id=q1.id, is_correct=1),
            models.PracticeRecord(user_id=user.id, question_id=q1.id, is_correct=0),
            models.PracticeRecord(user_id=user.id, question_id=q2.id, is_correct=1),
        ]
    )
    db_session.commit()

    rows = service.get_accuracy_by_tag(user_id=user.id)

    assert rows == [
        {
            "tag_id": service.repo.get_by_name("Java").id,
            "tag_name": "Java",
            "total_count": 3,
            "correct_count": 2,
            "accuracy_rate": 2 / 3,
        }
    ]


def test_question_tag_repository_removes_question_tags(db_session):
    user = _user(db_session)
    question = _question(db_session, user.id)
    tag = TagRepository(db_session).get_or_create(name="Java")
    repo = QuestionTagRepository(db_session)
    repo.add(question_id=question.id, tag_id=tag.id)

    removed = repo.clear_for_question(question.id)

    assert removed == 1
    assert repo.list_for_question(question.id) == []


def test_tags_api_requires_login(client):
    resp = client.get("/tags/")

    assert resp.status_code == 401


def test_tags_api_creates_lists_and_attaches_tags(client, auth_headers):
    course_resp = client.post(
        "/courses/",
        headers=auth_headers,
        json={"name": "Java", "description": "", "subject": "Java", "visibility": "private"},
    )
    assert course_resp.status_code == 201
    course_id = course_resp.json()["id"]

    create_resp = client.post(
        "/questions/",
        headers=auth_headers,
        json={
            "course_id": course_id,
            "type": "short_answer",
            "question": "Explain JVM",
            "answer": "Java Virtual Machine",
            "subject": "Java",
            "chapter": "Basics",
        },
    )
    assert create_resp.status_code == 201
    question_id = create_resp.json()["id"]

    tag_resp = client.post(
        f"/tags/questions/{question_id}",
        headers=auth_headers,
        json={"tag_names": ["Java", "Runtime", "Java"]},
    )
    assert tag_resp.status_code == 200
    assert [item["name"] for item in tag_resp.json()] == ["Java", "Runtime"]

    list_resp = client.get("/tags/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert [item["name"] for item in list_resp.json()["items"]] == ["Java", "Runtime"]

    question_tags_resp = client.get(f"/tags/questions/{question_id}", headers=auth_headers)
    assert question_tags_resp.status_code == 200
    assert [item["name"] for item in question_tags_resp.json()] == ["Java", "Runtime"]
