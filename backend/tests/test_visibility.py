"""Tests for question / course visibility isolation between users, and publish flow.

Covers all 7 permission requirements:
1. User A private → User B cannot see in /questions/ or /courses/
2. User A publishes course → User B can see in public library
3. User B cannot delete User A's questions
4. User A can delete their own private questions
5. Practice (/practice/random) only draws from visible-to-user questions
6. Wrong book is isolated per user
7. Import defaults to "private" visibility
"""


def _register_user(client, username: str, password: str = "pass"):
    """Helper: register and login a user, return auth headers."""
    client.post(
        "/auth/register",
        json={
            "username": username,
            "password": password,
            "invite_code": "dev-invite",
        },
    )
    r = client.post("/auth/login", json={"username": username, "password": password})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestVisibilityIsolation:
    """User A imports → User B cannot see; User A publishes → User B CAN see."""

    SAMPLE_QS = [
        {
            "type": "single_choice",
            "question": "A's secret Q?",
            "options": {"A": "a", "B": "b"},
            "answer": "A",
            "subject": "Private",
            "chapter": "Ch1",
        },
    ]

    def test_user_b_cannot_see_user_a_private_questions(self, client):
        """[Requirement 1] User A imports privately → User B sees none in /questions/."""
        alice = _register_user(client, "alice_iso")
        bob = _register_user(client, "bob_iso")

        # Alice imports a question (default: private, in "未分类题库")
        resp = client.post("/questions/batch", json=self.SAMPLE_QS, headers=alice)
        assert resp.status_code == 200

        # Alice sees her own question via /questions/my
        alice_my = client.get("/questions/my", headers=alice)
        assert len(alice_my.json()) == 1

        # Alice sees it via the general /questions/ (visibility filter shows own)
        alice_all = client.get("/questions/", headers=alice)
        assert len(alice_all.json()) == 1

        # Bob should NOT see Alice's private question via /questions/
        bob_all = client.get("/questions/", headers=bob)
        assert len(bob_all.json()) == 0

        # Bob should NOT see it via /questions/public either
        bob_pub = client.get("/questions/public", headers=bob)
        assert len(bob_pub.json()) == 0

        # Bob's /questions/my should also be empty
        bob_my = client.get("/questions/my", headers=bob)
        assert len(bob_my.json()) == 0

    def test_user_b_cannot_see_user_a_private_courses(self, client):
        """[Requirement 1] User A's private course is invisible to B in /courses/ listing."""
        alice = _register_user(client, "alice_crs")
        bob = _register_user(client, "bob_crs")

        # Alice creates a private course
        c_resp = client.post(
            "/courses/",
            json={
                "name": "Alice's Private Course",
                "visibility": "private",
            },
            headers=alice,
        )
        assert c_resp.status_code == 201
        cid = c_resp.json()["id"]

        # Bob's /courses/ listing should NOT contain it
        bob_list = client.get("/courses/", headers=bob).json()
        assert all(c["id"] != cid for c in bob_list)

        # Bob cannot access the course detail
        resp = client.get(f"/courses/{cid}", headers=bob)
        assert resp.status_code == 404

        # Bob cannot list its questions
        resp = client.get(f"/courses/{cid}/questions", headers=bob)
        assert resp.status_code == 404

    def test_user_b_can_see_after_publish(self, client):
        """[Requirements 2, 3, 4] Publish a question → B sees it; B cannot delete; A can delete."""
        alice = _register_user(client, "alice_pub")
        bob = _register_user(client, "bob_pub")

        # Alice imports a private question
        resp = client.post("/questions/batch", json=self.SAMPLE_QS, headers=alice)
        assert resp.status_code == 200
        qid = client.get("/questions/", headers=alice).json()[0]["id"]

        # Bob can't see it yet
        assert len(client.get("/questions/", headers=bob).json()) == 0

        # Alice publishes it
        resp = client.post(f"/questions/{qid}/publish", headers=alice)
        assert resp.status_code == 200
        assert resp.json()["visibility"] == "public"

        # Now Bob CAN see it via /questions/
        bob_all = client.get("/questions/", headers=bob)
        assert len(bob_all.json()) == 1
        assert bob_all.json()[0]["id"] == qid

        # Bob can also see it via /questions/public
        bob_pub = client.get("/questions/public", headers=bob)
        assert len(bob_pub.json()) == 1

        # Bob cannot delete Alice's question  [Requirement 3]
        resp = client.delete(f"/questions/{qid}", headers=bob)
        assert resp.status_code == 403

        # Alice can still delete her own question  [Requirement 4]
        resp = client.delete(f"/questions/{qid}", headers=alice)
        assert resp.status_code == 200

    def test_publish_entire_course(self, client):
        """[Requirement 2] Publishing an entire course makes questions visible to others."""
        alice = _register_user(client, "alice_cpub")
        bob = _register_user(client, "bob_cpub")

        # Alice creates a course and imports questions into it
        resp = client.post("/courses/", json={"name": "Alice's Course"}, headers=alice)
        cid = resp.json()["id"]

        qs = [
            {
                "type": "single_choice",
                "question": f"Course Q{i}?",
                "options": {"A": "a", "B": "b"},
                "answer": "A",
                "subject": "Test",
                "chapter": "Ch1",
                "course_id": cid,
            }
            for i in range(3)
        ]
        client.post("/questions/batch", json=qs, headers=alice)

        # Bob can't see the course or its questions
        resp = client.get(f"/courses/{cid}", headers=bob)
        assert resp.status_code == 404

        # Alice publishes the entire course
        resp = client.post(f"/courses/{cid}/publish", headers=alice)
        assert resp.status_code == 200
        assert resp.json()["visibility"] == "public"

        # Now Bob can access the course
        resp = client.get(f"/courses/{cid}", headers=bob)
        assert resp.status_code == 200

        # And Bob can see the course's questions
        resp = client.get(f"/courses/{cid}/questions", headers=bob)
        assert len(resp.json()) == 3

        # Bob still cannot delete the course
        resp = client.delete(f"/courses/{cid}", headers=bob)
        assert resp.status_code == 403


class TestPracticeVisibility:
    """[Requirement 5] Practice endpoints only draw from the current user's visible range."""

    SAMPLE_Q = {
        "type": "fill_blank",
        "question": "A's private question",
        "answer": "secret",
    }

    def test_user_a_can_practice_own_private_question(self, client):
        """User A sees their own private question via /practice/random."""
        alice = _register_user(client, "alice_prac")

        client.post("/questions/batch", json=[self.SAMPLE_Q], headers=alice)
        resp = client.get("/practice/random", headers=alice)
        assert resp.status_code == 200
        assert resp.json()["question"] == "A's private question"

    def test_user_b_gets_404_when_no_visible_questions(self, client):
        """User B gets 404 from /practice/random when only A's private questions exist."""
        alice = _register_user(client, "alice_prac2")
        bob = _register_user(client, "bob_prac")

        client.post("/questions/batch", json=[self.SAMPLE_Q], headers=alice)
        resp = client.get("/practice/random", headers=bob)
        assert resp.status_code == 404

    def test_user_b_can_practice_after_question_published(self, client):
        """After A publishes a question, B can get it via /practice/random."""
        alice = _register_user(client, "alice_prac3")
        bob = _register_user(client, "bob_prac2")

        client.post("/questions/batch", json=[self.SAMPLE_Q], headers=alice)
        qid = client.get("/questions/", headers=alice).json()[0]["id"]
        client.post(f"/questions/{qid}/publish", headers=alice)

        resp = client.get("/practice/random", headers=bob)
        assert resp.status_code == 200
        assert resp.json()["question"] == "A's private question"

    def test_user_b_cannot_submit_answer_to_invisible_question(self, client):
        """[Requirement 5] Submit on a question B cannot see — 404 (not visible)."""
        alice = _register_user(client, "alice_sub")
        bob = _register_user(client, "bob_sub")

        client.post("/questions/batch", json=[self.SAMPLE_Q], headers=alice)
        qid = client.get("/questions/", headers=alice).json()[0]["id"]

        # Bob tries to submit — question is private to A, so Bob gets 404
        resp = client.post(
            "/practice/submit",
            json={
                "question_id": qid,
                "user_answer": "guess",
            },
            headers=bob,
        )
        assert resp.status_code == 404


class TestWrongBookIsolation:
    """[Requirement 6] Wrong book records are isolated per user."""

    SAMPLE_Q = {
        "type": "fill_blank",
        "question": "Shared question for wrongbook test",
        "answer": "correct",
    }

    def test_wrongbook_per_user_isolation(self, client):
        """Wrong answers by User A do not appear in User B's wrongbook."""
        alice = _register_user(client, "alice_wb")
        bob = _register_user(client, "bob_wb")

        # Import as Alice (private)
        client.post("/questions/batch", json=[self.SAMPLE_Q], headers=alice)
        qid = client.get("/questions/", headers=alice).json()[0]["id"]

        # Alice submits wrong answer
        client.post(
            "/practice/submit",
            json={
                "question_id": qid,
                "user_answer": "wrong",
            },
            headers=alice,
        )

        # Alice's wrongbook has the record
        a_wb = client.get("/wrongbook/", headers=alice).json()
        assert len(a_wb) == 1
        assert a_wb[0]["question_id"] == qid

        # Bob's wrongbook is empty (Bob never submitted to this question)
        b_wb = client.get("/wrongbook/", headers=bob).json()
        assert len(b_wb) == 0

    def test_wrongbook_meta_per_user(self, client):
        """Wrongbook meta (subjects/chapters) is user-specific."""
        alice = _register_user(client, "alice_wb2")
        bob = _register_user(client, "bob_wb2")

        # Alice imports and gets a wrong record
        client.post("/questions/batch", json=[self.SAMPLE_Q], headers=alice)
        qid = client.get("/questions/", headers=alice).json()[0]["id"]
        client.post(
            "/practice/submit",
            json={
                "question_id": qid,
                "user_answer": "wrong",
            },
            headers=alice,
        )

        # Alice has meta
        a_meta = client.get("/wrongbook/meta", headers=alice).json()
        assert len(a_meta["subjects"]) >= 1

        # Bob has empty meta
        b_meta = client.get("/wrongbook/meta", headers=bob).json()
        assert b_meta["subjects"] == []
        assert b_meta["chapters"] == []


class TestImportDefaultsPrivate:
    """[Requirement 7] Import endpoints default to private visibility."""

    SAMPLE_Q = {
        "type": "fill_blank",
        "question": "Imported question",
        "answer": "ans",
    }

    def test_batch_import_defaults_private(self, client, auth_headers):
        """POST /questions/batch creates questions with visibility='private'."""
        client.post("/questions/batch", json=[self.SAMPLE_Q], headers=auth_headers)
        q = client.get("/questions/", headers=auth_headers).json()[0]
        assert q["visibility"] == "private"
        assert q["source"] == "import"

    def test_imported_question_has_owner(self, client, auth_headers):
        """Batch-imported questions get the importing user as owner_id."""
        client.post("/questions/batch", json=[self.SAMPLE_Q], headers=auth_headers)
        q = client.get("/questions/", headers=auth_headers).json()[0]
        assert q["owner_id"] is not None

    def test_file_auto_import_defaults_private(self, client, auth_headers):
        """POST /imports/file/auto creates questions with visibility='private'."""
        import json
        from unittest.mock import MagicMock, patch

        from backend.tests.test_imports import _make_docx_bytes

        content = _make_docx_bytes("Q: What is 1+1?\nA: 2")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "questions": [
                    {
                        "type": "fill_blank",
                        "question": "What is 1+1?",
                        "answer": "2",
                    }
                ]
            }
        )

        with patch("backend.routers.imports.OPENAI_API_KEY", "test-key"):
            with patch("backend.routers.imports.OpenAI") as mock_openai:
                mock_openai.return_value.chat.completions.create.return_value = mock_response
                resp = client.post(
                    "/imports/file/auto",
                    headers=auth_headers,
                    files={
                        "file": (
                            "test.docx",
                            content,
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
                    },
                )
        assert resp.status_code == 200
        # The question was imported to the user's default course
        q = client.get("/questions/", headers=auth_headers).json()[0]
        assert q["visibility"] == "private"
        assert q["source"] == "import"
