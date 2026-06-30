"""Tests for new endpoints: /courses/mine, course questions, course practice, publish, library."""


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
        client.post(
            "/auth/register",
            json={
                "username": "bob_mine",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "bob_mine", "password": "passpw"})
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
        client.post("/questions/batch", json=sample_questions, headers=auth_headers, params={"course_id": cid})

        resp = client.get(self.COURSES_MINE, headers=auth_headers)
        c = next(x for x in resp.json() if x["id"] == cid)
        assert c["question_count"] == 4

    def test_practice_count_increments(self, client, auth_headers, sample_questions):
        """practice_count and last_practiced_at should reflect submissions."""
        resp = client.post("/courses/", json={"name": "Practice Me"}, headers=auth_headers)
        cid = resp.json()["id"]
        client.post("/questions/batch", json=sample_questions, headers=auth_headers, params={"course_id": cid})

        # Get questions
        qq = client.get(f"/courses/{cid}/questions", headers=auth_headers).json()

        # Submit answers
        client.post(
            "/practice/submit",
            json={
                "question_id": qq[0]["id"],
                "user_answer": qq[0]["answer"],
            },
            headers=auth_headers,
        )
        client.post(
            "/practice/submit",
            json={
                "question_id": qq[1]["id"],
                "user_answer": "wrong",
            },
            headers=auth_headers,
        )

        resp = client.get(self.COURSES_MINE, headers=auth_headers)
        c = next(x for x in resp.json() if x["id"] == cid)
        assert c["practice_count"] == 2
        assert c["last_practiced_at"] is not None

    def test_practice_stats_per_user_isolation(self, client, auth_headers, sample_questions):
        """practice_count should only count the CURRENT user's practice."""
        resp = client.post("/courses/", json={"name": "Two Users"}, headers=auth_headers)
        cid = resp.json()["id"]
        client.post("/questions/batch", json=sample_questions, headers=auth_headers, params={"course_id": cid})

        # User A practices
        qq = client.get(f"/courses/{cid}/questions", headers=auth_headers).json()
        client.post(
            "/practice/submit",
            json={
                "question_id": qq[0]["id"],
                "user_answer": qq[0]["answer"],
            },
            headers=auth_headers,
        )

        # User A sees practice_count=1
        resp = client.get(self.COURSES_MINE, headers=auth_headers)
        c = next(x for x in resp.json() if x["id"] == cid)
        assert c["practice_count"] == 1

        # User B registers, but can't see User A's course at all via /mine
        client.post(
            "/auth/register",
            json={
                "username": "pc_iso",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "pc_iso", "password": "passpw"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(self.COURSES_MINE, headers=b_headers)
        assert resp.json() == []

    def test_public_course_logic_unchanged(self, client, auth_headers):
        """Own public courses should appear in /mine with correct counts."""
        resp = client.post(
            "/courses/",
            json={
                "name": "My Public",
                "visibility": "public",
            },
            headers=auth_headers,
        )
        cid = resp.json()["id"]

        # Add questions
        client.post(
            "/questions/batch",
            json=[
                {
                    "type": "fill_blank",
                    "question": "Q",
                    "answer": "A",
                    "course_id": cid,
                }
            ],
            headers=auth_headers,
        )

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
        client.post(
            "/auth/register",
            json={
                "username": "spy",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "spy", "password": "passpw"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(f"/courses/{cid}/questions", headers=b_headers)
        assert resp.status_code == 404

    def test_course_questions_paginated(self, client, auth_headers, sample_questions):
        resp = client.post("/courses/", json={"name": "Test"}, headers=auth_headers)
        cid = resp.json()["id"]
        for q in sample_questions:
            q["course_id"] = cid
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)

        resp = client.get(f"/courses/{cid}/questions", headers=auth_headers, params={"page": 1, "page_size": 2})
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

        client.post(
            "/auth/register",
            json={
                "username": "spy2",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "spy2", "password": "passpw"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(f"/courses/{cid}/practice/random", headers=b_headers)
        assert resp.status_code == 404


class TestPublish:
    def test_publish_question(self, client, auth_headers):
        client.post(
            "/questions/batch",
            json=[
                {
                    "type": "fill_blank",
                    "question": "Q?",
                    "answer": "A",
                }
            ],
            headers=auth_headers,
        )
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        resp = client.post(f"/questions/{qid}/publish", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["visibility"] == "public"

        # Verify other user can see it
        client.post(
            "/auth/register",
            json={
                "username": "viewer_pub",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "viewer_pub", "password": "passpw"})
        v_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get("/questions/", headers=v_headers)
        assert any(q["id"] == qid for q in resp.json())

    def test_publish_question_not_owner_forbidden(self, client, auth_headers):
        client.post(
            "/questions/batch",
            json=[
                {
                    "type": "fill_blank",
                    "question": "Q?",
                    "answer": "A",
                }
            ],
            headers=auth_headers,
        )
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        client.post(
            "/auth/register",
            json={
                "username": "pub_other",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "pub_other", "password": "passpw"})
        o_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.post(f"/questions/{qid}/publish", headers=o_headers)
        assert resp.status_code == 403

    def test_publish_question_already_published(self, client, auth_headers):
        client.post(
            "/questions/batch",
            json=[
                {
                    "type": "fill_blank",
                    "question": "Q?",
                    "answer": "A",
                }
            ],
            headers=auth_headers,
        )
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

        client.post(
            "/auth/register",
            json={
                "username": "pub_course",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "pub_course", "password": "passpw"})
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
