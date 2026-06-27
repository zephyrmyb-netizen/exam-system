"""Tests for spaced repetition review state updates and due queries."""

from datetime import UTC, datetime, timedelta

from backend import crud, models
from backend.crud import _compute_review_state


class TestReviewStateComputation:
    """Unit tests for the review state computation logic."""

    def test_first_answer_correct(self):
        now = datetime.now(UTC)
        state = _compute_review_state(is_correct=True, current=None, now=now)
        assert state["review_level"] == 1
        assert state["consecutive_correct"] == 1
        assert state["consecutive_wrong"] == 0
        assert state["review_mode"] == "spaced_repeat"
        assert state["next_review_at"] == now + timedelta(days=1)

    def test_first_answer_wrong(self):
        now = datetime.now(UTC)
        state = _compute_review_state(is_correct=False, current=None, now=now)
        assert state["review_level"] == 0
        assert state["consecutive_correct"] == 0
        assert state["consecutive_wrong"] == 1
        assert state["review_mode"] == "wrong_review"
        assert state["next_review_at"] == now + timedelta(minutes=10)

    def test_interval_progression(self):
        now = datetime.now(UTC)
        intervals = [1, 3, 7, 14, 30]
        for lvl in range(1, 6):
            current = models.UserQuestionReview(
                review_level=lvl - 1,
                consecutive_correct=lvl - 1,
                consecutive_wrong=0,
            )
            state = _compute_review_state(is_correct=True, current=current, now=now)
            assert state["review_level"] == lvl
            expected_days = intervals[min(lvl - 1, len(intervals) - 1)]
            assert state["next_review_at"] == now + timedelta(days=expected_days)

    def test_wrong_answer_resets(self):
        now = datetime.now(UTC)
        current = models.UserQuestionReview(
            review_level=3,
            consecutive_correct=3,
            consecutive_wrong=0,
        )
        state = _compute_review_state(is_correct=False, current=current, now=now)
        assert state["review_level"] == 0
        assert state["consecutive_correct"] == 0
        assert state["consecutive_wrong"] == 1
        assert state["review_mode"] == "wrong_review"

    def test_consecutive_wrong_increments(self):
        now = datetime.now(UTC)
        current = models.UserQuestionReview(
            review_level=0,
            consecutive_correct=0,
            consecutive_wrong=3,
        )
        state = _compute_review_state(is_correct=False, current=current, now=now)
        assert state["consecutive_wrong"] == 4


class TestReviewDB:
    """Integration tests for review state in the database."""

    QUESTIONS_BATCH = "/questions/batch"
    PRACTICE_SUBMIT = "/practice/submit"
    REVIEW_DUE = "/practice/review/due"
    REVIEW_TODAY = "/practice/review/today"

    def _setup(self, client, auth_headers):
        client.post(
            self.QUESTIONS_BATCH,
            json=[
                {
                    "type": "single_choice",
                    "question": "Q1: 1+1=?",
                    "options": {"A": "1", "B": "2"},
                    "answer": "B",
                    "subject": "数学",
                    "chapter": "第一章",
                },
                {
                    "type": "fill_blank",
                    "question": "Q2: capital of China",
                    "answer": "北京",
                    "subject": "地理",
                    "chapter": "第一章",
                },
                {
                    "type": "true_false",
                    "question": "Q3: Earth is round",
                    "answer": "正确",
                    "subject": "地理",
                    "chapter": "第二章",
                },
            ],
            headers=auth_headers,
        )
        resp = client.get("/questions/", headers=auth_headers)
        return {q["type"]: q for q in resp.json()}

    # ── Helpers ────────────────────────────────────────────────────────
    @staticmethod
    def _submit(client, auth_headers, qid, answer):
        return client.post(
            TestReviewDB.PRACTICE_SUBMIT,
            json={"question_id": qid, "user_answer": answer},
            headers=auth_headers,
        )

    # ── Tests ─────────────────────────────────────────────────────────
    def test_review_created_on_correct(self, client, auth_headers, db_session):
        qs = self._setup(client, auth_headers)
        qid = qs["single_choice"]["id"]
        self._submit(client, auth_headers, qid, "B")
        r = crud.get_user_question_review(db_session, user_id=1, question_id=qid)
        assert r is not None
        assert r.review_level == 1
        assert r.consecutive_correct == 1

    def test_level_progression(self, client, auth_headers, db_session):
        qs = self._setup(client, auth_headers)
        qid = qs["single_choice"]["id"]
        for _ in range(3):
            self._submit(client, auth_headers, qid, "B")
        r = crud.get_user_question_review(db_session, user_id=1, question_id=qid)
        assert r.review_level == 3
        assert r.consecutive_correct == 3

    def test_wrong_resets(self, client, auth_headers, db_session):
        qs = self._setup(client, auth_headers)
        qid = qs["single_choice"]["id"]
        for _ in range(2):
            self._submit(client, auth_headers, qid, "B")
        # Wrong answer
        self._submit(client, auth_headers, qid, "A")
        r = crud.get_user_question_review(db_session, user_id=1, question_id=qid)
        assert r.review_level == 0
        assert r.consecutive_correct == 0
        assert r.consecutive_wrong == 1

    def test_due_endpoint(self, client, auth_headers, db_session):
        qs = self._setup(client, auth_headers)
        qid = qs["single_choice"]["id"]
        # Submit wrong → due in 10 min
        self._submit(client, auth_headers, qid, "A")
        # Backdate to make it due now
        r = crud.get_user_question_review(db_session, user_id=1, question_id=qid)
        r.next_review_at = datetime.now(UTC) - timedelta(minutes=1)
        db_session.commit()
        # Due endpoint should return it
        resp = client.get(self.REVIEW_DUE, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_due_not_returned_future(self, client, auth_headers, db_session):
        qs = self._setup(client, auth_headers)
        qid = qs["single_choice"]["id"]
        # Correct → due in 1 day (future)
        self._submit(client, auth_headers, qid, "B")
        resp = client.get(self.REVIEW_DUE, headers=auth_headers)
        data = resp.json()
        assert not any(item.get("question", {}).get("id") == qid for item in data["items"])

    def test_user_isolation(self, client, auth_headers, db_session):
        qs = self._setup(client, auth_headers)
        qid = qs["single_choice"]["id"]
        self._submit(client, auth_headers, qid, "B")
        r = crud.get_user_question_review(db_session, user_id=999, question_id=qid)
        assert r is None

    def test_today_reflects_due(self, client, auth_headers, db_session):
        qs = self._setup(client, auth_headers)
        qid = qs["single_choice"]["id"]
        self._submit(client, auth_headers, qid, "A")
        r = crud.get_user_question_review(db_session, user_id=1, question_id=qid)
        r.next_review_at = datetime.now(UTC) - timedelta(minutes=1)
        db_session.commit()
        resp = client.get(self.REVIEW_TODAY, headers=auth_headers)
        data = resp.json()
        assert data["due_count"] >= 1
        assert data["wrong_count"] >= 1
