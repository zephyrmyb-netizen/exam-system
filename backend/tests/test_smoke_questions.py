"""Tests for new endpoints: /courses/mine, course questions, course practice, publish, library."""


class TestDeleteQuestion:
    def test_delete_own_question(self, client, auth_headers):
        client.post(
            "/questions/batch",
            json=[
                {
                    "type": "fill_blank",
                    "question": "Mine",
                    "answer": "A",
                }
            ],
            headers=auth_headers,
        )
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]
        resp = client.delete(f"/questions/{qid}", headers=auth_headers)
        assert resp.status_code == 200

    def test_delete_others_question_forbidden(self, client, auth_headers):
        client.post(
            "/questions/batch",
            json=[
                {
                    "type": "fill_blank",
                    "question": "A's",
                    "answer": "A",
                }
            ],
            headers=auth_headers,
        )
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        client.post(
            "/auth/register",
            json={
                "username": "delete_test",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "delete_test", "password": "passpw"})
        d_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.delete(f"/questions/{qid}", headers=d_headers)
        assert resp.status_code == 403

    def test_delete_nonexistent_question(self, client, auth_headers):
        resp = client.delete("/questions/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestManualCreateQuestion:
    QUESTIONS_URL = "/questions/"
    COURSES_URL = "/courses/"

    def test_manual_create_question(self, client, auth_headers):
        """POST /questions/ creates a single question with source=manual."""
        resp = client.post(self.COURSES_URL, json={"name": "My Course"}, headers=auth_headers)
        cid = resp.json()["id"]

        resp = client.post(
            self.QUESTIONS_URL,
            json={
                "course_id": cid,
                "type": "fill_blank",
                "question": "中国的首都是？",
                "answer": "北京",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source"] == "manual"
        assert data["visibility"] == "private"
        assert data["course_id"] == cid
        assert data["question"] == "中国的首都是？"

    def test_manual_create_requires_own_course(self, client, auth_headers):
        """Cannot create question in another user's course."""
        resp = client.post(self.COURSES_URL, json={"name": "A's Course"}, headers=auth_headers)
        cid = resp.json()["id"]

        client.post(
            "/auth/register",
            json={
                "username": "mc_other",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "mc_other", "password": "passpw"})
        bh = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.post(
            self.QUESTIONS_URL,
            json={
                "course_id": cid,
                "type": "fill_blank",
                "question": "Q",
                "answer": "A",
            },
            headers=bh,
        )
        assert resp.status_code == 403

    def test_manual_create_nonexistent_course(self, client, auth_headers):
        resp = client.post(
            self.QUESTIONS_URL,
            json={
                "course_id": 99999,
                "type": "fill_blank",
                "question": "Q",
                "answer": "A",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestEditQuestion:
    QUESTIONS_URL = "/questions/"
    QUESTIONS_BATCH = "/questions/batch"

    def test_edit_question(self, client, auth_headers):
        """PATCH /questions/{id} should update fields."""
        client.post(
            self.QUESTIONS_BATCH,
            json=[
                {
                    "type": "fill_blank",
                    "question": "Old Q",
                    "answer": "Old",
                }
            ],
            headers=auth_headers,
        )
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        resp = client.patch(
            f"{self.QUESTIONS_URL}{qid}",
            json={
                "question": "New Q",
                "answer": "New",
                "subject": "数学",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["question"] == "New Q"
        assert data["answer"] == "New"
        assert data["subject"] == "数学"

    def test_edit_question_not_owner(self, client, auth_headers):
        """Cannot edit another user's question."""
        client.post(
            self.QUESTIONS_BATCH,
            json=[
                {
                    "type": "fill_blank",
                    "question": "Q",
                    "answer": "A",
                }
            ],
            headers=auth_headers,
        )
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        client.post(
            "/auth/register",
            json={
                "username": "eq_other",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "eq_other", "password": "passpw"})
        bh = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.patch(f"{self.QUESTIONS_URL}{qid}", json={"question": "Hacked"}, headers=bh)
        assert resp.status_code == 403

    def test_edit_question_change_course(self, client, auth_headers):
        """Changing course_id should verify target course ownership."""
        resp = client.post("/courses/", json={"name": "C1"}, headers=auth_headers)
        c1 = resp.json()["id"]
        resp = client.post("/courses/", json={"name": "C2"}, headers=auth_headers)
        c2 = resp.json()["id"]

        client.post(
            self.QUESTIONS_BATCH,
            json=[
                {
                    "type": "fill_blank",
                    "question": "Q",
                    "answer": "A",
                    "course_id": c1,
                }
            ],
            headers=auth_headers,
        )
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        # Move to C2 (both owned)
        resp = client.patch(f"{self.QUESTIONS_URL}{qid}", json={"course_id": c2}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["course_id"] == c2

    def test_edit_question_change_course_not_own(self, client, auth_headers):
        """Changing course_id to another user's course is forbidden."""
        resp = client.post("/courses/", json={"name": "My C"}, headers=auth_headers)
        cid = resp.json()["id"]
        client.post(
            self.QUESTIONS_BATCH,
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
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        # Create course for user B
        client.post(
            "/auth/register",
            json={
                "username": "eqc_other",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "eqc_other", "password": "passpw"})
        bh = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.post("/courses/", json={"name": "B's C"}, headers=bh)
        bc = resp.json()["id"]

        # User A tries to move question to B's course
        resp = client.patch(f"{self.QUESTIONS_URL}{qid}", json={"course_id": bc}, headers=auth_headers)
        assert resp.status_code == 403

    def test_edit_nonexistent_question(self, client, auth_headers):
        resp = client.patch(f"{self.QUESTIONS_URL}99999", json={"question": "X"}, headers=auth_headers)
        assert resp.status_code == 404


class TestUnpublishQuestion:
    QUESTIONS_URL = "/questions/"
    QUESTIONS_BATCH = "/questions/batch"

    def test_unpublish_question(self, client, auth_headers):
        """POST /questions/{id}/unpublish should set visibility back to private."""
        client.post(
            self.QUESTIONS_BATCH,
            json=[
                {
                    "type": "fill_blank",
                    "question": "Q",
                    "answer": "A",
                }
            ],
            headers=auth_headers,
        )
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        # Publish
        client.post(f"{self.QUESTIONS_URL}{qid}/publish", headers=auth_headers)
        # Unpublish
        resp = client.post(f"{self.QUESTIONS_URL}{qid}/unpublish", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["visibility"] == "private"

    def test_unpublish_already_private(self, client, auth_headers):
        """Unpublish already private question returns 400."""
        client.post(
            self.QUESTIONS_BATCH,
            json=[
                {
                    "type": "fill_blank",
                    "question": "Q",
                    "answer": "A",
                }
            ],
            headers=auth_headers,
        )
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]
        resp = client.post(f"{self.QUESTIONS_URL}{qid}/unpublish", headers=auth_headers)
        assert resp.status_code == 400

    def test_unpublish_not_owner(self, client, auth_headers):
        """Cannot unpublish another user's question."""
        client.post(
            self.QUESTIONS_BATCH,
            json=[
                {
                    "type": "fill_blank",
                    "question": "Q",
                    "answer": "A",
                }
            ],
            headers=auth_headers,
        )
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]

        client.post(
            "/auth/register",
            json={
                "username": "uq_other",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "uq_other", "password": "passpw"})
        bh = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.post(f"{self.QUESTIONS_URL}{qid}/unpublish", headers=bh)
        assert resp.status_code == 403
