from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import models
from backend.api.exams import router as exams_router
from backend.auth import get_current_user
from backend.database import get_db


def _make_app(db_session, current_user=None) -> FastAPI:
    app = FastAPI()
    app.include_router(exams_router)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return app


def _make_user(db_session, username="exam_api_user", role_name=None, is_guest=False):
    role_id = None
    if role_name:
        role = models.Role(name=role_name)
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
        role_id = role.id
    user = models.User(username=username, password_hash="x", role_id=role_id, is_guest=1 if is_guest else 0)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_course(db_session, owner_id):
    course = models.QuestionBank(owner_id=owner_id, name="Exam API Course", created_at=datetime.now(UTC))
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


def _make_question(db_session, owner_id, course_id):
    question = models.Question(
        owner_id=owner_id,
        course_id=course_id,
        type="single_choice",
        question="1+1=?",
        options='{"A":"1","B":"2"}',
        answer="B",
        created_at=datetime.now(UTC),
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


def test_guest_can_create_publish_take_and_submit_exam(db_session):
    user = _make_user(db_session, is_guest=True)
    course = _make_course(db_session, user.id)
    question = _make_question(db_session, user.id, course.id)
    client = TestClient(_make_app(db_session, user))

    create_resp = client.post(
        "/exams/",
        json={"title": "API Exam", "course_id": course.id, "question_ids": [question.id], "total_score": 10},
    )
    assert create_resp.status_code == 201
    exam_id = create_resp.json()["id"]

    publish_resp = client.post(f"/exams/{exam_id}/publish")
    assert publish_resp.status_code == 200
    assert publish_resp.json()["status"] == "published"

    start_resp = client.post(f"/exams/{exam_id}/start")
    assert start_resp.status_code == 200
    assert start_resp.json()["exam_id"] == exam_id

    submit_resp = client.post(f"/exams/{exam_id}/submit", json={"answers": {str(question.id): "B"}})
    assert submit_resp.status_code == 200
    assert submit_resp.json()["score"] == 10
    assert submit_resp.json()["correct_count"] == 1


def test_exam_api_lists_only_published_exams(db_session):
    user = _make_user(db_session)
    course = _make_course(db_session, user.id)
    client = TestClient(_make_app(db_session, user))

    draft_id = client.post("/exams/", json={"title": "Draft", "course_id": course.id}).json()["id"]
    published_id = client.post("/exams/", json={"title": "Published", "course_id": course.id}).json()["id"]
    client.post(f"/exams/{published_id}/publish")

    response = client.get("/exams/")

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert published_id in ids
    assert draft_id not in ids


def test_exam_api_detail_returns_published_questions(db_session):
    user = _make_user(db_session, username="exam_detail_owner")
    course = _make_course(db_session, user.id)
    question = _make_question(db_session, user.id, course.id)
    client = TestClient(_make_app(db_session, user))
    exam_id = client.post(
        "/exams/",
        json={"title": "Detail Exam", "course_id": course.id, "question_ids": [question.id]},
    ).json()["id"]
    client.post(f"/exams/{exam_id}/publish")

    response = client.get(f"/exams/{exam_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == exam_id
    assert data["questions"][0]["question_id"] == question.id
    assert data["questions"][0]["options"] == {"A": "1", "B": "2"}


def test_exam_api_detail_hides_draft_from_other_users(db_session):
    owner = _make_user(db_session, username="exam_draft_owner")
    student = _make_user(db_session, username="exam_draft_student")
    course = _make_course(db_session, owner.id)
    question = _make_question(db_session, owner.id, course.id)
    owner_client = TestClient(_make_app(db_session, owner))
    exam_id = owner_client.post(
        "/exams/",
        json={"title": "Draft Detail", "course_id": course.id, "question_ids": [question.id]},
    ).json()["id"]
    student_client = TestClient(_make_app(db_session, student))

    response = student_client.get(f"/exams/{exam_id}")

    assert response.status_code == 404


def test_exam_api_leaderboard_returns_submitted_scores_sorted(db_session):
    owner = _make_user(db_session, username="leaderboard_owner")
    student_a = _make_user(db_session, username="leaderboard_student_a")
    student_b = _make_user(db_session, username="leaderboard_student_b")
    course = _make_course(db_session, owner.id)
    question = _make_question(db_session, owner.id, course.id)
    owner_client = TestClient(_make_app(db_session, owner))
    exam_id = owner_client.post(
        "/exams/",
        json={"title": "Leaderboard Exam", "course_id": course.id, "question_ids": [question.id], "total_score": 10},
    ).json()["id"]
    owner_client.post(f"/exams/{exam_id}/publish")

    student_a_client = TestClient(_make_app(db_session, student_a))
    student_b_client = TestClient(_make_app(db_session, student_b))
    student_a_client.post(f"/exams/{exam_id}/start")
    student_a_client.post(f"/exams/{exam_id}/submit", json={"answers": {str(question.id): "A"}})
    student_b_client.post(f"/exams/{exam_id}/start")
    student_b_client.post(f"/exams/{exam_id}/submit", json={"answers": {str(question.id): "B"}})

    response = student_a_client.get(f"/exams/{exam_id}/leaderboard")

    assert response.status_code == 200
    data = response.json()
    assert data["exam_id"] == exam_id
    assert data["total"] == 2
    assert [entry["username"] for entry in data["entries"]] == [student_b.username, student_a.username]
    assert [entry["score"] for entry in data["entries"]] == [10, 0]
    assert data["entries"][0]["rank"] == 1
    assert data["entries"][0]["total_score"] == 10


def test_exam_api_leaderboard_hides_draft_from_other_users(db_session):
    owner = _make_user(db_session, username="leaderboard_draft_owner")
    student = _make_user(db_session, username="leaderboard_draft_student")
    course = _make_course(db_session, owner.id)
    question = _make_question(db_session, owner.id, course.id)
    owner_client = TestClient(_make_app(db_session, owner))
    exam_id = owner_client.post(
        "/exams/",
        json={"title": "Draft Leaderboard", "course_id": course.id, "question_ids": [question.id]},
    ).json()["id"]
    student_client = TestClient(_make_app(db_session, student))

    response = student_client.get(f"/exams/{exam_id}/leaderboard")

    assert response.status_code == 404


def test_user_cannot_publish_someone_elses_exam(db_session):
    owner = _make_user(db_session, username="publish_owner")
    other_user = _make_user(db_session, username="publish_other")
    course = _make_course(db_session, owner.id)
    question = _make_question(db_session, owner.id, course.id)
    owner_client = TestClient(_make_app(db_session, owner))
    exam_id = owner_client.post(
        "/exams/",
        json={"title": "Private draft", "course_id": course.id, "question_ids": [question.id]},
    ).json()["id"]

    other_client = TestClient(_make_app(db_session, other_user))
    response = other_client.post(f"/exams/{exam_id}/publish")

    assert response.status_code == 403


def test_published_exam_share_code_resolves_to_the_real_exam(db_session):
    owner = _make_user(db_session, username="share_code_owner")
    visitor = _make_user(db_session, username="share_code_visitor")
    course = _make_course(db_session, owner.id)
    question = _make_question(db_session, owner.id, course.id)
    owner_client = TestClient(_make_app(db_session, owner))
    created = owner_client.post(
        "/exams/", json={"title": "Shared", "course_id": course.id, "question_ids": [question.id]}
    ).json()
    owner_client.post(f"/exams/{created['id']}/publish")

    response = TestClient(_make_app(db_session, visitor)).get(f"/exams/share/{created['share_code'].lower()}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["share_code"] == created["share_code"]


def test_exam_schedule_blocks_new_attempts_before_opening_and_after_deadline(db_session):
    owner = _make_user(db_session, username="schedule_owner")
    course = _make_course(db_session, owner.id)
    question = _make_question(db_session, owner.id, course.id)
    client = TestClient(_make_app(db_session, owner))
    now = datetime.now(UTC)
    future = client.post(
        "/exams/",
        json={
            "title": "Future", "course_id": course.id, "question_ids": [question.id],
            "start_at": (now + timedelta(hours=1)).isoformat(),
        },
    ).json()
    client.post(f"/exams/{future['id']}/publish")
    assert client.post(f"/exams/{future['id']}/start").status_code == 403

    closed = client.post(
        "/exams/",
        json={
            "title": "Closed", "course_id": course.id, "question_ids": [question.id],
            "end_at": (now - timedelta(minutes=1)).isoformat(),
        },
    ).json()
    client.post(f"/exams/{closed['id']}/publish")
    closed_response = client.post(f"/exams/{closed['id']}/start")
    assert closed_response.status_code == 403
    assert closed_response.json()["detail"] == "Exam is closed"


def test_exam_submission_can_add_only_wrong_answers_to_wrongbook(db_session):
    user = _make_user(db_session, username="exam_wrongbook_user")
    course = _make_course(db_session, user.id)
    question = _make_question(db_session, user.id, course.id)
    client = TestClient(_make_app(db_session, user))
    exam_id = client.post(
        "/exams/", json={"title": "Wrongbook", "course_id": course.id, "question_ids": [question.id]}
    ).json()["id"]
    client.post(f"/exams/{exam_id}/publish")
    client.post(f"/exams/{exam_id}/start")
    client.post(f"/exams/{exam_id}/submit", json={"answers": {str(question.id): "A"}})

    response = client.post(f"/exams/{exam_id}/wrongbook")

    assert response.status_code == 200
    assert response.json()["added_count"] == 1
    record = db_session.query(models.WrongRecord).filter_by(user_id=user.id, question_id=question.id).one()
    assert record.last_wrong_answer == "A"
