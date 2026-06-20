"""Tests for new endpoints: /courses/mine, course questions, course practice, publish, library."""
import pytest


class TestMyCourses:
    COURSES_MINE = "/courses/mine"

    def test_my_courses_empty(self, client, auth_headers):
        resp = client.get(self.COURSES_MINE, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_my_courses_only_own(self, client, auth_headers):
        """mine should only show own courses, not public ones created by others."""
        # User A creates courses
        client.post("/courses/", json={"name": "A1", "visibility": "private"}, headers=auth_headers)
        client.post("/courses/", json={"name": "A2", "visibility": "public"}, headers=auth_headers)

        resp = client.get(self.COURSES_MINE, headers=auth_headers)
        names = [c["name"] for c in resp.json()]
        assert "A1" in names
        assert "A2" in names
        assert len(resp.json()) == 2

    def test_my_courses_not_seeing_others(self, client, auth_headers):
        """mine should NOT show other users' courses."""
        # User A creates a course
        client.post("/courses/", json={"name": "A's Private"}, headers=auth_headers)

        # Register user B
        client.post("/auth/register", json={
            "username": "bob_mine", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "bob_mine", "password": "pass"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

        resp = client.get(self.COURSES_MINE, headers=b_headers)
        assert resp.json() == []

    def test_my_courses_pagination(self, client, auth_headers):
        for i in range(4):
            client.post("/courses/", json={"name": f"C{i}"}, headers=auth_headers)

        # Paginated
        resp = client.get(self.COURSES_MINE, headers=auth_headers, params={"page": 1, "page_size": 2})
        data = resp.json()
        assert isinstance(data, dict)
        assert data["total"] == 4
        assert len(data["items"]) == 2

    def test_question_count_empty_course(self, client, auth_headers):
        """New course should have question_count=0, practice_count=0."""
        client.post("/courses/", json={"name": "Empty"}, headers=auth_headers)
        resp = client.get(self.COURSES_MINE, headers=auth_headers)
        c = resp.json()[0]
        assert c["question_count"] == 0
        assert c["practice_count"] == 0
        assert c["last_practiced_at"] is None

    def test_question_count_with_questions(self, client, auth_headers, sample_questions):
        """question_count should reflect the number of questions in the course."""
        resp = client.post("/courses/", json={"name": "With Qs"}, headers=auth_headers)
        cid = resp.json()["id"]
        client.post("/questions/batch", json=sample_questions, headers=auth_headers,
                    params={"course_id": cid})

        resp = client.get(self.COURSES_MINE, headers=auth_headers)
        c = next(x for x in resp.json() if x["id"] == cid)
        assert c["question_count"] == 4

    def test_practice_count_increments(self, client, auth_headers, sample_questions):
        """practice_count and last_practiced_at should reflect submissions."""
        resp = client.post("/courses/", json={"name": "Practice Me"}, headers=auth_headers)
        cid = resp.json()["id"]
        client.post("/questions/batch", json=sample_questions, headers=auth_headers,
                    params={"course_id": cid})

        # Get questions
        qq = client.get(f"/courses/{cid}/questions", headers=auth_headers).json()

        # Submit answers
        client.post("/practice/submit", json={
            "question_id": qq[0]["id"], "user_answer": qq[0]["answer"],
        }, headers=auth_headers)
        client.post("/practice/submit", json={
            "question_id": qq[1]["id"], "user_answer": "wrong",
        }, headers=auth_headers)

        resp = client.get(self.COURSES_MINE, headers=auth_headers)
        c = next(x for x in resp.json() if x["id"] == cid)
        assert c["practice_count"] == 2
        assert c["last_practiced_at"] is not None

    def test_practice_stats_per_user_isolation(self, client, auth_headers, sample_questions):
        """practice_count should only count the CURRENT user's practice."""
        resp = client.post("/courses/", json={"name": "Two Users"}, headers=auth_headers)
        cid = resp.json()["id"]
        client.post("/questions/batch", json=sample_questions, headers=auth_headers,
                    params={"course_id": cid})

        # User A practices
        qq = client.get(f"/courses/{cid}/questions", headers=auth_headers).json()
        client.post("/practice/submit", json={
            "question_id": qq[0]["id"], "user_answer": qq[0]["answer"],
        }, headers=auth_headers)

        # User A sees practice_count=1
        resp = client.get(self.COURSES_MINE, headers=auth_headers)
        c = next(x for x in resp.json() if x["id"] == cid)
        assert c["practice_count"] == 1

        # User B registers, but can't see User A's course at all via /mine
        client.post("/auth/register", json={
            "username": "pc_iso", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "pc_iso", "password": "pass"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(self.COURSES_MINE, headers=b_headers)
        assert resp.json() == []

    def test_public_course_logic_unchanged(self, client, auth_headers):
        """Own public courses should appear in /mine with correct counts."""
        resp = client.post("/courses/", json={
            "name": "My Public", "visibility": "public",
        }, headers=auth_headers)
        cid = resp.json()["id"]

        # Add questions
        client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Q", "answer": "A", "course_id": cid,
        }], headers=auth_headers)

        resp = client.get(self.COURSES_MINE, headers=auth_headers)
        c = next(x for x in resp.json() if x["id"] == cid)
        assert c["question_count"] == 1
        assert c["visibility"] == "public"


class TestCourseQuestions:
    def test_course_questions_empty(self, client, auth_headers):
        resp = client.post("/courses/", json={"name": "Test"}, headers=auth_headers)
        cid = resp.json()["id"]
        resp = client.get(f"/courses/{cid}/questions", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_course_questions_with_questions(self, client, auth_headers, sample_questions):
        resp = client.post("/courses/", json={"name": "Test"}, headers=auth_headers)
        cid = resp.json()["id"]
        # Import questions into the course
        for q in sample_questions:
            q["course_id"] = cid
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)

        resp = client.get(f"/courses/{cid}/questions", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    def test_course_questions_not_accessible_by_others(self, client, auth_headers, sample_questions):
        """Other users should not see questions in a private course."""
        resp = client.post("/courses/", json={"name": "Private"}, headers=auth_headers)
        cid = resp.json()["id"]
        for q in sample_questions:
            q["course_id"] = cid
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)

        # User B tries to access
        client.post("/auth/register", json={
            "username": "spy", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "spy", "password": "pass"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(f"/courses/{cid}/questions", headers=b_headers)
        assert resp.status_code == 404

    def test_course_questions_paginated(self, client, auth_headers, sample_questions):
        resp = client.post("/courses/", json={"name": "Test"}, headers=auth_headers)
        cid = resp.json()["id"]
        for q in sample_questions:
            q["course_id"] = cid
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)

        resp = client.get(f"/courses/{cid}/questions", headers=auth_headers,
                          params={"page": 1, "page_size": 2})
        data = resp.json()
        assert isinstance(data, dict)
        assert data["total"] == 4
        assert len(data["items"]) == 2


class TestCoursePractice:
    def test_random_from_course(self, client, auth_headers, sample_questions):
        resp = client.post("/courses/", json={"name": "Test"}, headers=auth_headers)
        cid = resp.json()["id"]
        for q in sample_questions:
            q["course_id"] = cid
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)

        resp = client.get(f"/courses/{cid}/practice/random", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["course_id"] == cid

    def test_random_from_course_empty(self, client, auth_headers):
        resp = client.post("/courses/", json={"name": "Empty"}, headers=auth_headers)
        cid = resp.json()["id"]
        resp = client.get(f"/courses/{cid}/practice/random", headers=auth_headers)
        assert resp.status_code == 404

    def test_random_from_course_other_blocked(self, client, auth_headers, sample_questions):
        resp = client.post("/courses/", json={"name": "Private"}, headers=auth_headers)
        cid = resp.json()["id"]
        for q in sample_questions:
            q["course_id"] = cid
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)

        client.post("/auth/register", json={
            "username": "spy2", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "spy2", "password": "pass"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(f"/courses/{cid}/practice/random", headers=b_headers)
        assert resp.status_code == 404


class TestPublish:
    def test_publish_question(self, client, auth_headers):
        client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Q?", "answer": "A",
        }], headers=auth_headers)
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        resp = client.post(f"/questions/{qid}/publish", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["visibility"] == "public"

        # Verify other user can see it
        client.post("/auth/register", json={
            "username": "viewer_pub", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "viewer_pub", "password": "pass"})
        v_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get("/questions/", headers=v_headers)
        assert any(q["id"] == qid for q in resp.json())

    def test_publish_question_not_owner_forbidden(self, client, auth_headers):
        client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Q?", "answer": "A",
        }], headers=auth_headers)
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        client.post("/auth/register", json={
            "username": "pub_other", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "pub_other", "password": "pass"})
        o_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.post(f"/questions/{qid}/publish", headers=o_headers)
        assert resp.status_code == 403

    def test_publish_question_already_published(self, client, auth_headers):
        client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Q?", "answer": "A",
        }], headers=auth_headers)
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]
        client.post(f"/questions/{qid}/publish", headers=auth_headers)
        resp = client.post(f"/questions/{qid}/publish", headers=auth_headers)
        assert resp.status_code == 400

    def test_publish_course(self, client, auth_headers):
        resp = client.post("/courses/", json={"name": "Private Course"}, headers=auth_headers)
        cid = resp.json()["id"]
        assert resp.json()["visibility"] == "private"

        resp = client.post(f"/courses/{cid}/publish", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["visibility"] == "public"

    def test_publish_course_not_owner_forbidden(self, client, auth_headers):
        resp = client.post("/courses/", json={"name": "A's Course"}, headers=auth_headers)
        cid = resp.json()["id"]

        client.post("/auth/register", json={
            "username": "pub_course", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "pub_course", "password": "pass"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.post(f"/courses/{cid}/publish", headers=b_headers)
        assert resp.status_code == 403

    def test_publish_course_already_public(self, client, auth_headers):
        resp = client.post("/courses/", json={"name": "Pub", "visibility": "public"}, headers=auth_headers)
        cid = resp.json()["id"]
        resp = client.post(f"/courses/{cid}/publish", headers=auth_headers)
        assert resp.status_code == 400

    def test_publish_nonexistent_question(self, client, auth_headers):
        resp = client.post("/questions/99999/publish", headers=auth_headers)
        assert resp.status_code == 404


class TestLibrary:
    LIBRARY_PUBLIC = "/library/public"

    def test_library_public_empty(self, client, auth_headers):
        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_library_public_lists_public_courses(self, client, auth_headers):
        client.post("/courses/", json={"name": "Private", "visibility": "private"}, headers=auth_headers)
        client.post("/courses/", json={"name": "Public", "visibility": "public"}, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers)
        names = [c["name"] for c in resp.json()]
        assert "Public" in names
        assert "Private" not in names

    def test_library_public_course_questions(self, client, auth_headers, sample_questions):
        # Create a public course with questions
        resp = client.post("/courses/", json={"name": "PubCourse", "visibility": "public"}, headers=auth_headers)
        cid = resp.json()["id"]
        for q in sample_questions:
            q["course_id"] = cid
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)
        # Make questions public too
        for q in client.get(f"/courses/{cid}/questions", headers=auth_headers).json():
            client.post(f"/questions/{q['id']}/publish", headers=auth_headers)

        # Other user can see them via library
        client.post("/auth/register", json={
            "username": "lib_viewer", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "lib_viewer", "password": "pass"})
        v_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(f"{self.LIBRARY_PUBLIC}/{cid}/questions", headers=v_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    def test_library_private_course_not_found(self, client, auth_headers):
        """Private courses should not be accessible via /library/public/."""
        resp = client.post("/courses/", json={"name": "Secret", "visibility": "private"}, headers=auth_headers)
        cid = resp.json()["id"]

        client.post("/auth/register", json={
            "username": "lib_spy", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "lib_spy", "password": "pass"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(f"{self.LIBRARY_PUBLIC}/{cid}/questions", headers=b_headers)
        assert resp.status_code == 404

    def test_library_not_found(self, client, auth_headers):
        resp = client.get(f"{self.LIBRARY_PUBLIC}/99999/questions", headers=auth_headers)
        assert resp.status_code == 404

    def test_library_public_pagination(self, client, auth_headers):
        for i in range(3):
            client.post("/courses/", json={"name": f"Pub{i}", "visibility": "public"}, headers=auth_headers)
        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"page": 1, "page_size": 2})
        data = resp.json()
        assert isinstance(data, dict)
        assert data["total"] == 3
        assert len(data["items"]) == 2

    def test_library_keyword_search_name(self, client, auth_headers):
        """Keyword should match course name."""
        client.post("/courses/", json={"name": "高等数学", "visibility": "public"}, headers=auth_headers)
        client.post("/courses/", json={"name": "大学英语", "visibility": "public"}, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"keyword": "数学"})
        items = resp.json()
        assert len(items) == 1
        assert items[0]["name"] == "高等数学"

    def test_library_keyword_search_description(self, client, auth_headers):
        """Keyword should match course description."""
        client.post("/courses/", json={
            "name": "数学习题集",
            "description": "涵盖初中数学全部知识点",
            "visibility": "public",
        }, headers=auth_headers)
        client.post("/courses/", json={
            "name": "英语题库",
            "description": "四级考试真题",
            "visibility": "public",
        }, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"keyword": "初中"})
        items = resp.json()
        assert len(items) == 1
        assert items[0]["name"] == "数学习题集"

    def test_library_keyword_search_subject(self, client, auth_headers):
        """Keyword should match subject field."""
        client.post("/courses/", json={
            "name": "C1", "subject": "物理", "visibility": "public",
        }, headers=auth_headers)
        client.post("/courses/", json={
            "name": "C2", "subject": "化学", "visibility": "public",
        }, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"keyword": "物理"})
        items = resp.json()
        assert len(items) == 1
        assert items[0]["subject"] == "物理"

    def test_library_subject_filter_exact(self, client, auth_headers):
        """Subject param should do exact match."""
        client.post("/courses/", json={
            "name": "C1", "subject": "数学", "visibility": "public",
        }, headers=auth_headers)
        client.post("/courses/", json={
            "name": "C2", "subject": "物理", "visibility": "public",
        }, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"subject": "数学"})
        items = resp.json()
        assert len(items) == 1
        assert items[0]["subject"] == "数学"

    def test_library_keyword_no_match(self, client, auth_headers):
        """Keyword with no matches returns empty."""
        client.post("/courses/", json={"name": "数学", "visibility": "public"}, headers=auth_headers)
        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"keyword": "不存在的"})
        assert resp.json() == []

    def test_library_keyword_does_not_match_private(self, client, auth_headers):
        """Keyword should not return private courses."""
        client.post("/courses/", json={"name": "私有数学", "visibility": "private"}, headers=auth_headers)
        client.post("/courses/", json={"name": "公开数学", "visibility": "public"}, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"keyword": "数学"})
        names = [c["name"] for c in resp.json()]
        assert "公开数学" in names
        assert "私有数学" not in names


class TestDeleteQuestion:
    def test_delete_own_question(self, client, auth_headers):
        client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Mine", "answer": "A",
        }], headers=auth_headers)
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]
        resp = client.delete(f"/questions/{qid}", headers=auth_headers)
        assert resp.status_code == 200

    def test_delete_others_question_forbidden(self, client, auth_headers):
        client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "A's", "answer": "A",
        }], headers=auth_headers)
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        client.post("/auth/register", json={
            "username": "delete_test", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "delete_test", "password": "pass"})
        d_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.delete(f"/questions/{qid}", headers=d_headers)
        assert resp.status_code == 403

    def test_delete_nonexistent_question(self, client, auth_headers):
        resp = client.delete("/questions/99999", headers=auth_headers)
        assert resp.status_code == 404


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
        # newest first → correct (submitted later) then wrong
        assert items[0]["is_correct"] is True
        assert items[1]["is_correct"] is False
        # Verify answered_at is descending (newest first)
        from datetime import datetime
        t0 = datetime.fromisoformat(items[0]["answered_at"])
        t1 = datetime.fromisoformat(items[1]["answered_at"])
        assert t0 >= t1  # newer record first

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
        assert data["due_count"] == 1
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


class TestDeleteCourseComplete:
    """[Goal] Comprehensive course deletion tests: cascade, history, isolation."""

    COURSES_URL = "/courses/"
    QUESTIONS_BATCH = "/questions/batch"
    PRACTICE_SUBMIT = "/practice/submit"
    PRACTICE_HISTORY = "/practice/history"
    LIBRARY_PUBLIC = "/library/public"

    def _register_user(self, client, username):
        client.post("/auth/register", json={
            "username": username, "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": username, "password": "pass"})
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def test_delete_empty_course(self, client, auth_headers):
        """Delete an empty course should succeed."""
        resp = client.post(self.COURSES_URL, json={"name": "Empty"}, headers=auth_headers)
        cid = resp.json()["id"]
        resp = client.delete(f"{self.COURSES_URL}{cid}", headers=auth_headers)
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

        # Verify it's gone
        resp = client.get(f"{self.COURSES_URL}{cid}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_course_with_questions(self, client, auth_headers, sample_questions):
        """Deleting a course should cascade-delete its questions."""
        resp = client.post(self.COURSES_URL, json={"name": "With Qs"}, headers=auth_headers)
        cid = resp.json()["id"]
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers,
                    params={"course_id": cid})

        # Verify questions exist
        before = client.get(f"/courses/{cid}/questions", headers=auth_headers).json()
        assert len(before) == 4

        # Delete
        client.delete(f"{self.COURSES_URL}{cid}", headers=auth_headers)

        # Course gone
        resp = client.get(f"{self.COURSES_URL}{cid}", headers=auth_headers)
        assert resp.status_code == 404

        # Questions gone (not visible)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        assert all(q.get("course_id") != cid for q in questions)

    def test_delete_course_cleans_wrongbook(self, client, auth_headers, sample_questions):
        """Wrong records should be cleaned up when course is deleted."""
        resp = client.post(self.COURSES_URL, json={"name": "Wrong Me"}, headers=auth_headers)
        cid = resp.json()["id"]
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers,
                    params={"course_id": cid})

        questions = client.get(f"/courses/{cid}/questions", headers=auth_headers).json()
        # Submit wrong answers
        for q in questions[:2]:
            client.post(self.PRACTICE_SUBMIT, json={
                "question_id": q["id"], "user_answer": "WRONG",
            }, headers=auth_headers)

        # Verify wrongbook has entries
        wb = client.get("/wrongbook/", headers=auth_headers).json()
        assert len(wb) >= 2

        # Delete course
        client.delete(f"{self.COURSES_URL}{cid}", headers=auth_headers)

        # Wrongbook should be empty (or not contain those questions)
        wb = client.get("/wrongbook/", headers=auth_headers).json()
        deleted_qids = {q["id"] for q in questions}
        assert all(r["question_id"] not in deleted_qids for r in wb if isinstance(r, dict))

    def test_delete_course_keeps_practice_history(self, client, auth_headers, sample_questions):
        """Practice history should survive course deletion without errors."""
        resp = client.post(self.COURSES_URL, json={"name": "History Keep"}, headers=auth_headers)
        cid = resp.json()["id"]
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers,
                    params={"course_id": cid})

        questions = client.get(f"/courses/{cid}/questions", headers=auth_headers).json()
        # Submit answers
        for q in questions[:2]:
            client.post(self.PRACTICE_SUBMIT, json={
                "question_id": q["id"], "user_answer": q["answer"],
            }, headers=auth_headers)

        # Verify practice history has entries
        hist = client.get(self.PRACTICE_HISTORY, headers=auth_headers).json()
        assert hist["total"] >= 2

        # Delete course
        client.delete(f"{self.COURSES_URL}{cid}", headers=auth_headers)

        # Practice history should NOT error
        hist = client.get(self.PRACTICE_HISTORY, headers=auth_headers)
        assert hist.status_code == 200

    def test_delete_public_course_removed_from_library(self, client, auth_headers):
        """Deleting a public course should remove it from the public library."""
        resp = client.post(self.COURSES_URL, json={
            "name": "Public Delete", "visibility": "public",
        }, headers=auth_headers)
        cid = resp.json()["id"]

        # Exists in library
        lib = client.get(self.LIBRARY_PUBLIC, headers=auth_headers).json()
        assert any(c["id"] == cid for c in lib)

        # Delete
        client.delete(f"{self.COURSES_URL}{cid}", headers=auth_headers)

        # Gone from library
        lib = client.get(self.LIBRARY_PUBLIC, headers=auth_headers).json()
        assert all(c["id"] != cid for c in lib)

    def test_delete_others_course_returns_403(self, client, auth_headers):
        """Non-owner cannot delete another user's course."""
        resp = client.post(self.COURSES_URL, json={"name": "Not Yours"}, headers=auth_headers)
        cid = resp.json()["id"]

        # User B tries
        b_headers = self._register_user(client, "del_other")
        resp = client.delete(f"{self.COURSES_URL}{cid}", headers=b_headers)
        assert resp.status_code == 403
        assert "只能删除" in resp.json()["detail"]

    def test_delete_nonexistent_course_returns_404(self, client, auth_headers):
        """Deleting a non-existent course returns 404."""
        resp = client.delete(f"{self.COURSES_URL}99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_courses_mine_clean_after_delete(self, client, auth_headers):
        """After deleting own course, /courses/mine should not list it."""
        resp = client.post(self.COURSES_URL, json={"name": "Mine Delete"}, headers=auth_headers)
        cid = resp.json()["id"]

        assert any(c["id"] == cid for c in client.get("/courses/mine", headers=auth_headers).json())

        client.delete(f"{self.COURSES_URL}{cid}", headers=auth_headers)

        mine = client.get("/courses/mine", headers=auth_headers).json()
        assert all(c["id"] != cid for c in mine)
