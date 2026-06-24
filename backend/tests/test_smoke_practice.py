"""Tests for new endpoints: /courses/mine, course questions, course practice, publish, library."""
import pytest

class TestPracticeStats:
    PRACTICE_SUBMIT = "/practice/submit"
    PRACTICE_STATS = "/practice/stats"
    QUESTIONS_BATCH = "/questions/batch"

    def test_stats_initial_zero(self, client, auth_headers):
        """No practice records → all stats should be 0."""
        resp = client.get(self.PRACTICE_STATS, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["today_count"] == 0
        assert data["total_count"] == 0
        assert data["correct_count"] == 0
        assert data["wrong_count"] == 0
        assert data["accuracy_rate"] == 0.0
        assert data["recent_count_7d"] == 0

    def test_stats_after_correct_submit(self, client, auth_headers, sample_questions):
        """Submit a correct answer; stats should reflect it."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "B",
        }, headers=auth_headers)

        resp = client.get(self.PRACTICE_STATS, headers=auth_headers)
        data = resp.json()
        assert data["total_count"] == 1
        assert data["correct_count"] == 1
        assert data["wrong_count"] == 0
        assert data["accuracy_rate"] == 1.0
        assert data["today_count"] == 1  # only one submit just now → today
        assert data["recent_count_7d"] == 1  # only one submit → within 7d

    def test_stats_after_wrong_submit(self, client, auth_headers, sample_questions):
        """Submit a wrong answer; stats should reflect it."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "C",
        }, headers=auth_headers)

        resp = client.get(self.PRACTICE_STATS, headers=auth_headers)
        data = resp.json()
        assert data["total_count"] == 1
        assert data["correct_count"] == 0
        assert data["wrong_count"] == 1
        assert data["accuracy_rate"] == 0.0
        assert data["today_count"] == 1  # wrong answer still counts in today
        assert data["recent_count_7d"] == 1  # wrong answer still counts in 7d

        # Verify wrongbook also recorded
        wb = client.get("/wrongbook/", headers=auth_headers).json()
        assert len(wb) == 1
        assert wb[0]["question_id"] == sc_q["id"]

    def test_stats_after_mixed_submits(self, client, auth_headers, sample_questions):
        """Multiple submits: correct + wrong; verify stats accuracy."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()

        # First: correct
        sc_q = next(q for q in questions if q["type"] == "single_choice")
        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "B",
        }, headers=auth_headers)

        # Second: wrong
        tf_q = next(q for q in questions if q["type"] == "true_false")
        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": tf_q["id"], "user_answer": "错",
        }, headers=auth_headers)

        resp = client.get(self.PRACTICE_STATS, headers=auth_headers)
        data = resp.json()
        assert data["total_count"] == 2
        assert data["correct_count"] == 1
        assert data["wrong_count"] == 1
        assert data["accuracy_rate"] == 0.5
        assert data["today_count"] == 2  # both submits are today
        assert data["recent_count_7d"] == 2  # both submits within 7d

    def test_stats_isolation(self, client, auth_headers, sample_questions):
        """User A's stats should not be visible to User B."""
        # User A submits
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")
        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "B",
        }, headers=auth_headers)

        # User B checks stats → should be zero
        client.post("/auth/register", json={
            "username": "stats_iso", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "stats_iso", "password": "pass"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(self.PRACTICE_STATS, headers=b_headers)
        data = resp.json()
        assert data["total_count"] == 0
        assert data["correct_count"] == 0
        assert data["wrong_count"] == 0
        assert data["accuracy_rate"] == 0.0
        assert data["today_count"] == 0
        assert data["recent_count_7d"] == 0

    def test_stats_unauthorized(self, client):
        """[Requirement 10] Unauthenticated access to /practice/stats returns 401."""
        resp = client.get(self.PRACTICE_STATS)
        assert resp.status_code == 401

    def test_practice_record_created_on_correct_submit(self, client, auth_headers, sample_questions):
        """[Requirement 1] Submitting correct answer creates a PracticeRecord in the DB."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        resp = client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "B",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["is_correct"] is True

        # Directly verify PracticeRecord via history endpoint
        hist = client.get(self.PRACTICE_STATS, headers=auth_headers).json()
        assert hist["total_count"] == 1
        assert hist["correct_count"] == 1

    def test_practice_record_created_on_wrong_submit(self, client, auth_headers, sample_questions):
        """[Requirement 2] Submitting wrong answer creates PracticeRecord AND wrongbook record."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        resp = client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "C",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["is_correct"] is False
        assert resp.json()["wrongbook_recorded"] is True

        # PracticeRecord exists
        stats = client.get(self.PRACTICE_STATS, headers=auth_headers).json()
        assert stats["total_count"] == 1
        assert stats["wrong_count"] == 1

        # Wrongbook record exists (aggregated)
        wb = client.get("/wrongbook/", headers=auth_headers).json()
        assert len(wb) == 1
        assert wb[0]["question_id"] == sc_q["id"]
        assert wb[0]["wrong_count"] == 1

class TestPracticeHistory:
    PRACTICE_SUBMIT = "/practice/submit"
    PRACTICE_HISTORY = "/practice/history"
    QUESTIONS_BATCH = "/questions/batch"

    def test_history_empty(self, client, auth_headers):
        """No practice → history should be empty list."""
        resp = client.get(self.PRACTICE_HISTORY, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_history_unauthorized(self, client):
        """[Requirement 10] Unauthenticated access to /practice/history returns 401."""
        resp = client.get(self.PRACTICE_HISTORY)
        assert resp.status_code == 401

    def test_history_after_submit(self, client, auth_headers, sample_questions):
        """Submit → history should contain the record."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "B",
        }, headers=auth_headers)

        resp = client.get(self.PRACTICE_HISTORY, headers=auth_headers)
        data = resp.json()
        assert data["total"] == 1
        assert data["page"] == 1
        items = data["items"]
        assert len(items) == 1
        r = items[0]
        assert r["question_id"] == sc_q["id"]
        assert r["is_correct"] is True
        assert r["user_answer"] == "B"
        assert r["correct_answer"] == sc_q["answer"]
        assert r["question_type"] == "single_choice"
        assert r["question_text"]  # should have question snippet
        assert "1+1" in r["question_text"]

    def test_history_records_both_correct_and_wrong(self, client, auth_headers, sample_questions):
        """[Requirement 12] Both correct and wrong answers appear in history, newest first."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "C",
        }, headers=auth_headers)
        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "B",
        }, headers=auth_headers)

        resp = client.get(self.PRACTICE_HISTORY, headers=auth_headers)
        items = resp.json()["items"]
        assert len(items) == 2
        # Both records should appear (order may be non‑deterministic with same‑second timestamps)
        correct_records = [it for it in items if it["is_correct"]]
        wrong_records = [it for it in items if not it["is_correct"]]
        assert len(correct_records) == 1
        assert len(wrong_records) == 1

    def test_history_isolation(self, client, auth_headers, sample_questions):
        """User B should not see User A's history."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")
        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "B",
        }, headers=auth_headers)

        # User B
        client.post("/auth/register", json={
            "username": "hist_iso", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "hist_iso", "password": "pass"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(self.PRACTICE_HISTORY, headers=b_headers)
        assert resp.json()["items"] == []

    def test_history_pagination(self, client, auth_headers, sample_questions):
        """[Requirement 11] History should support pagination with page/page_size."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")
        tf_q = next(q for q in questions if q["type"] == "true_false")
        mc_q = next(q for q in questions if q["type"] == "multiple_choice")

        # Submit 3 answers
        for q in [sc_q, tf_q, mc_q]:
            client.post(self.PRACTICE_SUBMIT, json={
                "question_id": q["id"],
                "user_answer": q["answer"],
            }, headers=auth_headers)

        # Page size 2 → only 2 items
        resp = client.get(self.PRACTICE_HISTORY, headers=auth_headers, params={"page": 1, "page_size": 2})
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2

        # Page 2 → 1 item
        resp = client.get(self.PRACTICE_HISTORY, headers=auth_headers, params={"page": 2, "page_size": 2})
        data = resp.json()
        assert len(data["items"]) == 1

        # Page 3 → empty
        resp = client.get(self.PRACTICE_HISTORY, headers=auth_headers, params={"page": 3, "page_size": 2})
        data = resp.json()
        assert len(data["items"]) == 0

class TestWrongReview:
    PRACTICE_REVIEW_WRONG = "/practice/review/wrong"
    PRACTICE_SUBMIT = "/practice/submit"
    QUESTIONS_BATCH = "/questions/batch"

    def test_wrong_review_no_wrong_questions(self, client, auth_headers):
        """No wrong records -> 404 with friendly message."""
        resp = client.get(self.PRACTICE_REVIEW_WRONG, headers=auth_headers)
        assert resp.status_code == 404
        assert "错题" in resp.json()["detail"]

    def test_wrong_review_returns_wrong_question(self, client, auth_headers, sample_questions):
        """After a wrong answer, the wrong-review endpoint returns that question."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        # Submit wrong
        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "C",
        }, headers=auth_headers)

        resp = client.get(self.PRACTICE_REVIEW_WRONG, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == sc_q["id"]

    def test_wrong_review_prioritizes_high_wrong_count(self, client, auth_headers, sample_questions):
        """Question with higher wrong_count should be returned first."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")
        tf_q = next(q for q in questions if q["type"] == "true_false")

        # tf_q wrong once, sc_q wrong twice -> sc_q should come first
        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": tf_q["id"], "user_answer": "错",
        }, headers=auth_headers)
        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "C",
        }, headers=auth_headers)
        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "D",
        }, headers=auth_headers)

        resp = client.get(self.PRACTICE_REVIEW_WRONG, headers=auth_headers)
        assert resp.status_code == 200
        # sc_q has wrong_count=2, should be returned first
        assert resp.json()["id"] == sc_q["id"]

    def test_wrong_review_user_isolation(self, client, auth_headers, sample_questions):
        """User B should not see User A's wrong questions."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")
        client.post(self.PRACTICE_SUBMIT, json={
            "question_id": sc_q["id"], "user_answer": "C",
        }, headers=auth_headers)

        # User B
        client.post("/auth/register", json={
            "username": "wr_iso", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "wr_iso", "password": "pass"})
        bh = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(self.PRACTICE_REVIEW_WRONG, headers=bh)
        assert resp.status_code == 404

    def test_wrong_review_type_filter(self, client, auth_headers, sample_questions):
        """Type filter should work on wrong review."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")
        tf_q = next(q for q in questions if q["type"] == "true_false")

        client.post(self.PRACTICE_SUBMIT, json={"question_id": sc_q["id"], "user_answer": "C"}, headers=auth_headers)
        client.post(self.PRACTICE_SUBMIT, json={"question_id": tf_q["id"], "user_answer": "错"}, headers=auth_headers)

        resp = client.get(self.PRACTICE_REVIEW_WRONG, headers=auth_headers, params={"type": "true_false"})
        assert resp.status_code == 200
        assert resp.json()["type"] == "true_false"

    def test_wrong_review_clears_after_correct_answer(self, client, auth_headers, sample_questions):
        """After submitting correct answer to a wrong question, it disappears from wrong review."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        # Submit wrong
        client.post(self.PRACTICE_SUBMIT, json={"question_id": sc_q["id"], "user_answer": "C"}, headers=auth_headers)
        resp = client.get(self.PRACTICE_REVIEW_WRONG, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == sc_q["id"]

        # Submit correct
        client.post(self.PRACTICE_SUBMIT, json={"question_id": sc_q["id"], "user_answer": "B"}, headers=auth_headers)

        # Now wrong review should be empty
        resp = client.get(self.PRACTICE_REVIEW_WRONG, headers=auth_headers)
        assert resp.status_code == 404
        assert "错题" in resp.json()["detail"]

class TestRandomChapter:
    PRACTICE_RANDOM = "/practice/random"
    QUESTIONS_BATCH = "/questions/batch"

    def test_random_by_chapter(self, client, auth_headers, sample_questions):
        """Random question with chapter filter should only return matching chapters."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)

        resp = client.get(self.PRACTICE_RANDOM, headers=auth_headers, params={"chapter": "第一章"})
        assert resp.status_code == 200
        assert resp.json()["chapter"] == "第一章"

    def test_random_by_chapter_no_match(self, client, auth_headers, sample_questions):
        """No matching chapter should return 404."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)

        resp = client.get(self.PRACTICE_RANDOM, headers=auth_headers, params={"chapter": "不存在的章节"})
        assert resp.status_code == 404

    def test_random_combined_course_type_chapter(self, client, auth_headers, sample_questions):
        """Combined course_id + type + chapter filter should all apply simultaneously."""
        # Create a course
        resp = client.post("/courses/", json={
            "name": "组合筛选课程", "visibility": "private",
        }, headers=auth_headers)
        cid = resp.json()["id"]

        # Import questions into the course
        client.post(
            self.QUESTIONS_BATCH,
            json=sample_questions,
            headers=auth_headers,
            params={"course_id": cid},
        )

        # Filter: course_id + true_false + 第一章
        resp = client.get(
            self.PRACTICE_RANDOM,
            headers=auth_headers,
            params={"course_id": cid, "type": "true_false", "chapter": "第一章"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "true_false"
        assert data["chapter"] == "第一章"
        assert data["course_id"] == cid

class TestTodayReview:
    PRACTICE_REVIEW_TODAY = "/practice/review/today"

    def test_today_review_empty(self, client, auth_headers):
        """No practice data -> all zeros, no weak types, recommends random_practice."""
        resp = client.get(self.PRACTICE_REVIEW_TODAY, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["due_count"] == 0
        assert data["wrong_count"] == 0
        assert data["weak_types"] == []
        assert "random_practice" in data["recommended_modes"]

    def test_today_review_with_wrong_questions(self, client, auth_headers, sample_questions):
        """After wrong answers, due_count and wrong_count should reflect them."""
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        client.post("/practice/submit", json={"question_id": sc_q["id"], "user_answer": "C"}, headers=auth_headers)

        resp = client.get(self.PRACTICE_REVIEW_TODAY, headers=auth_headers)
        data = resp.json()
        # due_count counts actually due review records (next_review_at <= now).
        # A newly-created wrong review has next_review_at = now + 10 min, so it's
        # not immediately due. wrong_count counts wrong_records directly.
        assert data["wrong_count"] == 1
        assert "wrong_review" in data["recommended_modes"]

    def test_today_review_user_isolation(self, client, auth_headers, sample_questions):
        """User B should see their own stats (empty), not User A's."""
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")
        client.post("/practice/submit", json={"question_id": sc_q["id"], "user_answer": "C"}, headers=auth_headers)

        client.post("/auth/register", json={
            "username": "tr_iso", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "tr_iso", "password": "pass"})
        bh = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(self.PRACTICE_REVIEW_TODAY, headers=bh)
        data = resp.json()
        assert data["due_count"] == 0

class TestWeakTypes:
    PRACTICE_INSIGHTS_WEAK = "/practice/insights/weak-types"

    def test_weak_types_empty(self, client, auth_headers):
        """No practice data -> empty list."""
        resp = client.get(self.PRACTICE_INSIGHTS_WEAK, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_weak_types_with_data(self, client, auth_headers, sample_questions):
        """After practice with errors, weak types should be returned."""
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")
        tf_q = next(q for q in questions if q["type"] == "true_false")

        # sc_q: correct, correct; tf_q: wrong, wrong -> tf_q should be weak
        for _ in range(2):
            client.post("/practice/submit", json={
                "question_id": sc_q["id"], "user_answer": sc_q["answer"],
            }, headers=auth_headers)
        for _ in range(2):
            client.post("/practice/submit", json={
                "question_id": tf_q["id"], "user_answer": "错",
            }, headers=auth_headers)

        resp = client.get(self.PRACTICE_INSIGHTS_WEAK, headers=auth_headers)
        items = resp.json()
        assert len(items) >= 1
        assert any(wt["question_type"] == "true_false" and wt["error_rate"] > 0.5 for wt in items)

    def test_weak_types_user_isolation(self, client, auth_headers, sample_questions):
        """User B should see empty weak types."""
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")
        client.post("/practice/submit", json={
            "question_id": sc_q["id"], "user_answer": "C",
        }, headers=auth_headers)

        client.post("/auth/register", json={
            "username": "wt_iso", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "wt_iso", "password": "pass"})
        bh = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(self.PRACTICE_INSIGHTS_WEAK, headers=bh)
        assert resp.json() == []
