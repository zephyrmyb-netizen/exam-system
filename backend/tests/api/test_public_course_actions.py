from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import models
from backend.auth import get_current_user
from backend.database import get_db
from backend.routers.library import router as library_router


def _app(db_session, user):
    app = FastAPI()
    app.include_router(library_router)
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: user
    return app


def _user(db_session, name):
    user = models.User(username=name, password_hash="x")
    db_session.add(user)
    db_session.commit()
    return user


def _public_course(db_session, owner_id):
    course = models.QuestionBank(owner_id=owner_id, name="Public", visibility="public", created_at=datetime.now(UTC))
    db_session.add(course)
    db_session.commit()
    question = models.Question(
        owner_id=owner_id, course_id=course.id, visibility="public", type="single_choice",
        question="2+2?", answer="B", options='{"A":"3","B":"4"}', created_at=datetime.now(UTC),
    )
    db_session.add(question)
    db_session.commit()
    return course, question


def test_public_course_copy_favorite_and_report_are_persisted(db_session):
    owner = _user(db_session, "public_actions_owner")
    user = _user(db_session, "public_actions_user")
    course, question = _public_course(db_session, owner.id)
    client = TestClient(_app(db_session, user))

    copy = client.post(f"/library/public/{course.id}/copy")
    favorite = client.post(f"/library/public/{course.id}/favorite")
    report = client.post(f"/library/public/{course.id}/report", json={"reason": "wrong_content", "detail": "answer is wrong"})

    assert copy.status_code == 201
    copied_id = copy.json()["copied_course_id"]
    copied = db_session.get(models.QuestionBank, copied_id)
    assert copied.owner_id == user.id
    assert copied.visibility == "private"
    assert db_session.query(models.Question).filter_by(course_id=copied_id).count() == 1
    assert favorite.json()["favorited"] is True
    assert db_session.query(models.CourseFavorite).filter_by(course_id=course.id, user_id=user.id).count() == 1
    assert report.status_code == 201
    assert db_session.query(models.CourseReport).filter_by(course_id=course.id, reporter_id=user.id).one().detail == "answer is wrong"
    assert question.id > 0
