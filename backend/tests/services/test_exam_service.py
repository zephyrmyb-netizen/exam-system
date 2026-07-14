from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from backend import models, schemas
from backend.services.exam_service import ExamService


def _make_user(db_session, username="exam_user"):
    user = models.User(username=username, password_hash="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_course(db_session, owner_id, name="Exam Course"):
    course = models.QuestionBank(owner_id=owner_id, name=name, created_at=datetime.now(UTC))
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


def _make_question(db_session, owner_id, course_id, answer="B"):
    question = models.Question(
        owner_id=owner_id,
        course_id=course_id,
        type="single_choice",
        question="1+1=?",
        options='{"A":"1","B":"2"}',
        answer=answer,
        created_at=datetime.now(UTC),
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


def test_create_exam_requires_owned_course(db_session):
    owner = _make_user(db_session, "exam_course_owner")
    other = _make_user(db_session, "exam_course_other")
    course = _make_course(db_session, owner.id)
    service = ExamService(db_session)

    with pytest.raises(HTTPException) as exc:
        service.create_exam(schemas.ExamCreate(title="Nope", course_id=course.id), creator_id=other.id)

    assert exc.value.status_code == 403


def test_publish_exam_and_start_attempt(db_session):
    user = _make_user(db_session)
    course = _make_course(db_session, user.id)
    question = _make_question(db_session, user.id, course.id)
    service = ExamService(db_session)

    exam = service.create_exam(
        schemas.ExamCreate(title="Quiz", course_id=course.id, question_ids=[question.id]),
        creator_id=user.id,
    )
    published = service.publish_exam(exam.id, user.id)
    attempt = service.start_attempt(exam.id, user.id)

    assert published.status == "published"
    assert attempt.exam_id == exam.id
    assert attempt.submitted_at is None


def test_submit_scores_correct_and_wrong_answers(db_session):
    user = _make_user(db_session)
    course = _make_course(db_session, user.id)
    question = _make_question(db_session, user.id, course.id, answer="B")
    service = ExamService(db_session)
    exam = service.create_exam(
        schemas.ExamCreate(title="Quiz", course_id=course.id, question_ids=[question.id], total_score=10),
        creator_id=user.id,
    )
    service.publish_exam(exam.id, user.id)
    service.start_attempt(exam.id, user.id)

    result = service.submit_exam(exam.id, user.id, schemas.ExamSubmissionCreate(answers={str(question.id): "B"}))

    assert result.score == 10
    assert result.correct_count == 1
    assert result.wrong_count == 0
    assert result.accuracy_rate == 100


def test_student_cannot_start_draft_exam(db_session):
    user = _make_user(db_session)
    course = _make_course(db_session, user.id)
    service = ExamService(db_session)
    exam = service.create_exam(schemas.ExamCreate(title="Draft", course_id=course.id), creator_id=user.id)

    with pytest.raises(HTTPException) as exc:
        service.start_attempt(exam.id, user.id)

    assert exc.value.status_code == 404
