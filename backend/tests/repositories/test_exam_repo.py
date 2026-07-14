from datetime import UTC, datetime

from backend import models, schemas
from backend.repositories.exam_repo import ExamRepository


def _make_user(db_session, username="exam_owner"):
    user = models.User(username=username, password_hash="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_course(db_session, owner_id):
    course = models.QuestionBank(owner_id=owner_id, name="Exam Bank", created_at=datetime.now(UTC))
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


def _make_question(db_session, owner_id, course_id, text="1+1=?", answer="B"):
    question = models.Question(
        owner_id=owner_id,
        course_id=course_id,
        type="single_choice",
        question=text,
        options='{"A":"1","B":"2"}',
        answer=answer,
        created_at=datetime.now(UTC),
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


def test_create_exam_with_questions(db_session):
    user = _make_user(db_session)
    course = _make_course(db_session, user.id)
    q1 = _make_question(db_session, user.id, course.id, "Q1")
    q2 = _make_question(db_session, user.id, course.id, "Q2")
    repo = ExamRepository(db_session)

    exam = repo.create_exam(
        schemas.ExamCreate(title="Mock exam", course_id=course.id, question_ids=[q1.id, q2.id]),
        creator_id=user.id,
    )

    assert exam.title == "Mock exam"
    assert exam.status == "draft"
    assert [item.question_id for item in exam.questions] == [q1.id, q2.id]


def test_list_published_exams_visible_to_students(db_session):
    user = _make_user(db_session)
    course = _make_course(db_session, user.id)
    repo = ExamRepository(db_session)
    draft = repo.create_exam(schemas.ExamCreate(title="Draft", course_id=course.id), creator_id=user.id)
    published = repo.create_exam(schemas.ExamCreate(title="Published", course_id=course.id), creator_id=user.id)
    repo.update_status(published.id, "published")

    items, total = repo.list_published()

    assert total == 1
    assert items[0].id == published.id
    assert draft.id not in {item.id for item in items}


def test_create_submission_and_get_existing_attempt(db_session):
    user = _make_user(db_session)
    course = _make_course(db_session, user.id)
    repo = ExamRepository(db_session)
    exam = repo.create_exam(schemas.ExamCreate(title="Published", course_id=course.id), creator_id=user.id)

    submission = repo.create_submission(exam_id=exam.id, user_id=user.id)
    again = repo.get_active_submission(exam_id=exam.id, user_id=user.id)

    assert submission.id == again.id
    assert submission.submitted_at is None
