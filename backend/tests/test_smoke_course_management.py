"""Tests for new endpoints: /courses/mine, course questions, course practice, publish, library."""


class TestDeleteCourseComplete:
    """[Goal] Comprehensive course deletion tests: cascade, history, isolation."""

    COURSES_URL = "/courses/"
    QUESTIONS_BATCH = "/questions/batch"
    PRACTICE_SUBMIT = "/practice/submit"
    PRACTICE_HISTORY = "/practice/history"
    LIBRARY_PUBLIC = "/library/public"

    def _register_user(self, client, username):
        client.post(
            "/auth/register",
            json={
                "username": username,
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": username, "password": "passpw"})
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
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers, params={"course_id": cid})

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
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers, params={"course_id": cid})

        questions = client.get(f"/courses/{cid}/questions", headers=auth_headers).json()
        # Submit wrong answers
        for q in questions[:2]:
            client.post(
                self.PRACTICE_SUBMIT,
                json={
                    "question_id": q["id"],
                    "user_answer": "WRONG",
                },
                headers=auth_headers,
            )

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
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers, params={"course_id": cid})

        questions = client.get(f"/courses/{cid}/questions", headers=auth_headers).json()
        # Submit answers
        for q in questions[:2]:
            client.post(
                self.PRACTICE_SUBMIT,
                json={
                    "question_id": q["id"],
                    "user_answer": q["answer"],
                },
                headers=auth_headers,
            )

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
        resp = client.post(
            self.COURSES_URL,
            json={
                "name": "Public Delete",
                "visibility": "public",
            },
            headers=auth_headers,
        )
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


class TestEditCourse:
    COURSES_URL = "/courses/"

    def test_edit_course(self, client, auth_headers):
        """PATCH /courses/{id} should update name, description, subject."""
        resp = client.post(self.COURSES_URL, json={"name": "Old"}, headers=auth_headers)
        cid = resp.json()["id"]

        resp = client.patch(
            f"{self.COURSES_URL}{cid}",
            json={
                "name": "New",
                "description": "Desc",
                "subject": "Math",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New"
        assert data["description"] == "Desc"
        assert data["subject"] == "Math"

    def test_edit_course_empty_name(self, client, auth_headers):
        """Name cannot be empty."""
        resp = client.post(self.COURSES_URL, json={"name": "X"}, headers=auth_headers)
        cid = resp.json()["id"]
        resp = client.patch(f"{self.COURSES_URL}{cid}", json={"name": "  "}, headers=auth_headers)
        assert resp.status_code == 400

    def test_edit_course_not_owner(self, client, auth_headers):
        """Cannot edit another user's course."""
        resp = client.post(self.COURSES_URL, json={"name": "A's"}, headers=auth_headers)
        cid = resp.json()["id"]

        client.post(
            "/auth/register",
            json={
                "username": "ec_other",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "ec_other", "password": "passpw"})
        bh = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.patch(f"{self.COURSES_URL}{cid}", json={"name": "Hacked"}, headers=bh)
        assert resp.status_code == 403

    def test_edit_course_partial(self, client, auth_headers):
        """Only name changed, other fields unchanged."""
        resp = client.post(
            self.COURSES_URL,
            json={
                "name": "Old",
                "description": "Old Desc",
                "subject": "Old Subj",
            },
            headers=auth_headers,
        )
        cid = resp.json()["id"]

        resp = client.patch(f"{self.COURSES_URL}{cid}", json={"name": "New"}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New"
        assert data["description"] == "Old Desc"
        assert data["subject"] == "Old Subj"


class TestUnpublishCourse:
    COURSES_URL = "/courses/"

    def test_unpublish_course(self, client, auth_headers):
        """POST /courses/{id}/unpublish sets course and questions to private."""
        resp = client.post(
            self.COURSES_URL,
            json={
                "name": "Public",
                "visibility": "public",
            },
            headers=auth_headers,
        )
        cid = resp.json()["id"]

        # Add a public question
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
        qid = client.get(f"/courses/{cid}/questions", headers=auth_headers).json()[0]["id"]
        client.post(f"/questions/{qid}/publish", headers=auth_headers)

        # Unpublish course
        resp = client.post(f"{self.COURSES_URL}{cid}/unpublish", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["visibility"] == "private"

        # Question should also be private
        q = client.get("/questions/", headers=auth_headers).json()
        assert any(x["id"] == qid and x["visibility"] == "private" for x in q)

    def test_unpublish_already_private(self, client, auth_headers):
        """Unpublish private course returns 400."""
        resp = client.post(self.COURSES_URL, json={"name": "P"}, headers=auth_headers)
        cid = resp.json()["id"]
        resp = client.post(f"{self.COURSES_URL}{cid}/unpublish", headers=auth_headers)
        assert resp.status_code == 400

    def test_unpublish_not_owner(self, client, auth_headers):
        """Cannot unpublish another user's course."""
        resp = client.post(
            self.COURSES_URL,
            json={
                "name": "A's",
                "visibility": "public",
            },
            headers=auth_headers,
        )
        cid = resp.json()["id"]

        client.post(
            "/auth/register",
            json={
                "username": "uc_other",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "uc_other", "password": "passpw"})
        bh = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.post(f"{self.COURSES_URL}{cid}/unpublish", headers=bh)
        assert resp.status_code == 403
