"""Phase 4 M2 coverage for recommendations and analytics."""

from datetime import UTC, datetime, timedelta

from backend import models
from backend.services.analytics_service import AnalyticsService
from backend.services.recommendation_service import RecommendationService
from backend.services.tag_service import TagService


def _user(db_session, username="alice"):
    user = models.User(username=username, password_hash="hash")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _course(db_session, owner_id, name="Java"):
    course = models.QuestionBank(owner_id=owner_id, name=name, visibility="private")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


def _question(db_session, owner_id, course_id=None, text="What is JVM?", q_type="single_choice"):
    question = models.Question(
        owner_id=owner_id,
        course_id=course_id,
        type=q_type,
        question=text,
        options='{"A":"A","B":"B"}' if q_type in ("single_choice", "multiple_choice") else None,
        answer="A",
        subject="Java",
        chapter="Basics",
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


def _practice(
    db_session,
    user_id,
    question,
    *,
    is_correct,
    answered_at=None,
    user_answer="B",
):
    record = models.PracticeRecord(
        user_id=user_id,
        question_id=question.id,
        course_id=question.course_id,
        question_type=question.type,
        is_correct=1 if is_correct else 0,
        user_answer=user_answer,
        correct_answer=question.answer,
        answered_at=answered_at or datetime.now(UTC),
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


def test_today_recommendation_includes_weak_tags_and_modes(db_session):
    user = _user(db_session)
    course = _course(db_session, user.id)
    question = _question(db_session, user.id, course.id)
    TagService(db_session).tag_question(question_id=question.id, tag_names=["Java"])
    _practice(db_session, user.id, question, is_correct=False)
    _practice(db_session, user.id, question, is_correct=False)
    _practice(db_session, user.id, question, is_correct=True)

    rec = RecommendationService(db_session).get_today_recommendation(user_id=user.id)

    assert rec["weak_tags"][0]["tag_name"] == "Java"
    assert rec["weak_tags"][0]["accuracy_rate"] == 1 / 3
    assert "weak_tag_practice" in rec["recommended_modes"]


def test_today_recommendation_includes_due_reviews(db_session):
    user = _user(db_session)
    question = _question(db_session, user.id)
    db_session.add(
        models.UserQuestionReview(
            user_id=user.id,
            question_id=question.id,
            next_review_at=datetime.now(UTC) - timedelta(days=1),
            review_level=1,
            review_mode="spaced_repeat",
        )
    )
    db_session.commit()

    rec = RecommendationService(db_session).get_today_recommendation(user_id=user.id)

    assert rec["due_count"] == 1
    assert rec["due_question_ids"] == [question.id]
    assert "spaced_repeat" in rec["recommended_modes"]


def test_weak_questions_order_by_wrong_count(db_session):
    user = _user(db_session)
    first = _question(db_session, user.id, text="Weak Q1")
    second = _question(db_session, user.id, text="Weak Q2")
    _practice(db_session, user.id, first, is_correct=False)
    _practice(db_session, user.id, first, is_correct=False)
    _practice(db_session, user.id, second, is_correct=False)

    weak = RecommendationService(db_session).get_weak_questions(user_id=user.id, limit=10)

    assert [question.id for question in weak] == [first.id, second.id]


def test_recommendations_api_requires_login(client):
    response = client.get("/recommendations/today")

    assert response.status_code == 401


def test_recommendations_api_returns_today_payload(client, auth_headers):
    response = client.get("/recommendations/today", headers=auth_headers)

    assert response.status_code == 200
    assert "recommended_modes" in response.json()


def test_analytics_daily_activity_zero_fills_days(db_session):
    user = _user(db_session)
    question = _question(db_session, user.id)
    _practice(db_session, user.id, question, is_correct=True, answered_at=datetime.now(UTC))

    rows = AnalyticsService(db_session).get_daily_activity(user_id=user.id, days=3)

    assert len(rows) == 3
    assert rows[-1]["count"] == 1
    assert set(rows[0].keys()) == {"date", "count"}


def test_analytics_type_distribution_counts_correct_answers(db_session):
    user = _user(db_session)
    choice = _question(db_session, user.id, q_type="single_choice")
    blank = _question(db_session, user.id, text="Blank", q_type="fill_blank")
    _practice(db_session, user.id, choice, is_correct=True)
    _practice(db_session, user.id, choice, is_correct=False)
    _practice(db_session, user.id, blank, is_correct=True, user_answer="A")

    rows = AnalyticsService(db_session).get_type_distribution(user_id=user.id)

    by_type = {row["question_type"]: row for row in rows}
    assert by_type["single_choice"]["total_count"] == 2
    assert by_type["single_choice"]["correct_count"] == 1
    assert by_type["fill_blank"]["accuracy_rate"] == 1.0


def test_analytics_streak_counts_consecutive_practice_days(db_session):
    user = _user(db_session)
    question = _question(db_session, user.id)
    now = datetime.now(UTC)
    _practice(db_session, user.id, question, is_correct=True, answered_at=now)
    _practice(db_session, user.id, question, is_correct=True, answered_at=now - timedelta(days=1))
    _practice(db_session, user.id, question, is_correct=True, answered_at=now - timedelta(days=2))

    streak = AnalyticsService(db_session).get_streak(user_id=user.id)

    assert streak["current_streak"] == 3


def test_analytics_api_requires_login(client):
    response = client.get("/analytics/daily-activity")

    assert response.status_code == 401


def test_analytics_api_returns_type_distribution(client, auth_headers):
    response = client.get("/analytics/type-distribution", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []
