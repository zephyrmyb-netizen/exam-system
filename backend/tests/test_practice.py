"""Tests for practice endpoints: random, submit with normalization."""


class TestPractice:
    PRACTICE_RANDOM = "/practice/random"
    PRACTICE_SUBMIT = "/practice/submit"
    QUESTIONS_BATCH = "/questions/batch"

    def test_random_no_questions(self, client, auth_headers):
        resp = client.get(self.PRACTICE_RANDOM, headers=auth_headers)
        assert resp.status_code == 404
        assert "为空" in resp.json()["detail"]

    def test_random_question(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get(self.PRACTICE_RANDOM, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "question" in data
        assert "type" in data

    def test_random_question_by_type(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        # Filter by single_choice
        resp = client.get(self.PRACTICE_RANDOM + "?type=single_choice", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "single_choice"

        # Filter by true_false
        resp = client.get(self.PRACTICE_RANDOM + "?type=true_false", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "true_false"

    def test_random_question_by_type_no_match(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get(self.PRACTICE_RANDOM + "?type=short_answer", headers=auth_headers)
        assert resp.status_code == 404

    def test_random_question_excludes_answered_ids(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        remaining = questions[0]
        excluded_ids = ",".join(str(question["id"]) for question in questions[1:])

        resp = client.get(
            self.PRACTICE_RANDOM,
            headers=auth_headers,
            params={"exclude_ids": excluded_ids},
        )

        assert resp.status_code == 200
        assert resp.json()["id"] == remaining["id"]

    def test_random_question_returns_404_when_all_ids_excluded(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        excluded_ids = ",".join(str(question["id"]) for question in questions)

        resp = client.get(
            self.PRACTICE_RANDOM,
            headers=auth_headers,
            params={"exclude_ids": excluded_ids},
        )

        assert resp.status_code == 404

    def test_wrong_review_excludes_answered_ids(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        first, second = questions[0], questions[1]

        for question in (first, second):
            resp = client.post(
                self.PRACTICE_SUBMIT,
                json={"question_id": question["id"], "user_answer": "__wrong__"},
                headers=auth_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["is_correct"] is False

        resp = client.get(
            "/practice/review/wrong",
            headers=auth_headers,
            params={"exclude_ids": str(first["id"])},
        )

        assert resp.status_code == 200
        assert resp.json()["id"] == second["id"]

    def test_submit_correct_single_choice(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        resp = client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "b",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is True
        assert data["correct_answer"] == "B"
        assert data["wrongbook_recorded"] is False

    def test_submit_correct_true_false(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        tf_q = next(q for q in questions if q["type"] == "true_false")

        resp = client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": tf_q["id"],
                "user_answer": "对",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is True
        assert data["correct_answer"] == "True"
        assert data["wrongbook_recorded"] is False

    def test_submit_wrong(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        resp = client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "C",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is False
        assert data["correct_answer"] == "B"
        assert data["wrongbook_recorded"] is True

    def test_submit_wrong_twice(self, client, auth_headers, sample_questions):
        """Submit wrong twice; still wrongbook_recorded=True, count increments."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        # First wrong
        client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "C",
            },
            headers=auth_headers,
        )
        # Second wrong
        resp = client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "D",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is False
        assert data["wrongbook_recorded"] is True
        # Verify wrong_count=2 via wrongbook endpoint
        wb = client.get("/wrongbook/", headers=auth_headers).json()
        rec = next(r for r in wb if r["question_id"] == sc_q["id"])
        assert rec["wrong_count"] == 2

    def test_submit_correct_after_wrong(self, client, auth_headers, sample_questions):
        """Submit wrong, then correct; wrongbook_recorded=False, record cleared."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        # First wrong
        client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "C",
            },
            headers=auth_headers,
        )
        # Then correct
        resp = client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "B",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is True
        assert data["wrongbook_recorded"] is False
        # Verify record is removed
        wb = client.get("/wrongbook/", headers=auth_headers).json()
        assert all(r["question_id"] != sc_q["id"] for r in wb)

    def test_submit_nonexistent_question(self, client, auth_headers):
        resp = client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": 99999,
                "user_answer": "A",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_submit_multiple_choice_normalized(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        mc_q = next(q for q in questions if q["type"] == "multiple_choice")

        resp = client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": mc_q["id"],
                "user_answer": '["A","C"]',
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is True


class TestPracticeWithCourses:
    """Tests for /practice/random?course_id= filtering."""

    PRACTICE_RANDOM = "/practice/random"
    QUESTIONS_BATCH = "/questions/batch"
    COURSES_URL = "/courses/"

    def test_random_with_course_id(self, client, auth_headers, sample_questions):
        """GET /practice/random?course_id=X should return a question from that course."""
        # Create a course
        resp = client.post(
            self.COURSES_URL,
            json={
                "name": "测试课程",
                "visibility": "private",
            },
            headers=auth_headers,
        )
        cid = resp.json()["id"]

        # Import questions into the course
        client.post(
            self.QUESTIONS_BATCH,
            json=sample_questions,
            headers=auth_headers,
            params={"course_id": cid},
        )

        # Get random from course
        resp = client.get(
            self.PRACTICE_RANDOM,
            headers=auth_headers,
            params={"course_id": cid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "question" in data
        assert data["course_id"] == cid

    def test_random_with_course_id_and_type_filter(self, client, auth_headers, sample_questions):
        """course_id + type filter should both apply."""
        resp = client.post(
            self.COURSES_URL,
            json={
                "name": "类型筛选课程",
            },
            headers=auth_headers,
        )
        cid = resp.json()["id"]

        client.post(
            self.QUESTIONS_BATCH,
            json=sample_questions,
            headers=auth_headers,
            params={"course_id": cid},
        )

        resp = client.get(
            self.PRACTICE_RANDOM,
            headers=auth_headers,
            params={"course_id": cid, "type": "true_false"},
        )
        assert resp.status_code == 200
        assert resp.json()["type"] == "true_false"

    def test_random_with_course_id_empty(self, client, auth_headers):
        """Course with no questions should return 404."""
        resp = client.post(
            self.COURSES_URL,
            json={
                "name": "空课程",
            },
            headers=auth_headers,
        )
        cid = resp.json()["id"]

        resp = client.get(
            self.PRACTICE_RANDOM,
            headers=auth_headers,
            params={"course_id": cid},
        )
        assert resp.status_code == 404
        assert "无可用题目" in resp.json()["detail"]

    def test_random_with_course_id_unauthorized(self, client, auth_headers, sample_questions):
        """User B should not be able to draw from User A's private course."""
        # User A creates a private course with questions
        resp = client.post(
            self.COURSES_URL,
            json={
                "name": "私有课程",
                "visibility": "private",
            },
            headers=auth_headers,
        )
        cid = resp.json()["id"]

        client.post(
            self.QUESTIONS_BATCH,
            json=sample_questions,
            headers=auth_headers,
            params={"course_id": cid},
        )

        # Register and login as user B
        client.post(
            "/auth/register",
            json={
                "username": "intruder",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        resp = client.post("/auth/login", json={"username": "intruder", "password": "passpw"})
        b_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        # User B tries to access user A's private course
        resp = client.get(
            self.PRACTICE_RANDOM,
            headers=b_headers,
            params={"course_id": cid},
        )
        assert resp.status_code == 404
        assert "不存在" in resp.json()["detail"]

    def test_random_with_course_id_nonexistent(self, client, auth_headers):
        """Non-existent course should return 404."""
        resp = client.get(
            self.PRACTICE_RANDOM,
            headers=auth_headers,
            params={"course_id": 99999},
        )
        assert resp.status_code == 404
        assert "不存在" in resp.json()["detail"]
