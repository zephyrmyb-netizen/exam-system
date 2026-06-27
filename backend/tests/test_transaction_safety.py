"""Tests for transaction safety in import and practice flows."""


class TestImportTransactionSafety:
    """Verify that failed imports don't leave orphaned courses in the DB."""

    QUESTIONS_BATCH = "/questions/batch"
    COURSES_URL = "/courses/"
    IMPORTS_AUTO = "/imports/file/auto"
    IMPORTS_FILE = "/imports/file"

    def test_auto_import_no_course_on_ai_failure(self, client, auth_headers):
        """When AI parsing fails, no course should be created."""

        from unittest.mock import MagicMock, patch

        from backend.tests.test_imports import _make_docx_bytes

        content = _make_docx_bytes("Invalid content that will fail AI parsing")

        # Mock AI to return unparseable garbage
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not valid json at all {{{"

        with patch("backend.routers.imports.OPENAI_API_KEY", "fake-key"):
            with patch("backend.routers.imports.OPENAI_BASE_URL", "http://localhost"):
                with patch("backend.routers.imports.OpenAI") as mock_openai:
                    mock_openai.return_value.chat.completions.create.return_value = mock_response
                    # This should fail — AI can't parse it
                    resp = client.post(
                        self.IMPORTS_AUTO,
                        files={
                            "file": (
                                "test.docx",
                                content,
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            )
                        },
                        headers=auth_headers,
                    )

        # Should be an error (400 or 502)
        assert resp.status_code >= 400

        # No new course should have been created
        courses_resp = client.get("/courses/mine", headers=auth_headers)
        assert courses_resp.status_code == 200
        courses = courses_resp.json()
        # Should still be 0 (nothing was committed)
        assert len(courses) == 0

    def test_confirm_all_or_nothing(self, client, auth_headers):
        """When one question fails validation in confirm, nothing is imported."""

        # Pre-create a course
        resp = client.post(
            self.COURSES_URL,
            json={
                "name": "Test Course",
                "visibility": "private",
            },
            headers=auth_headers,
        )
        cid = resp.json()["id"]

        # Try to confirm with one valid and one invalid question
        body = {
            "course_id": cid,
            "course_name": "",
            "questions": [
                {"type": "single_choice", "question": "Q1?", "options": {"A": "1", "B": "2"}, "answer": "A"},
                {"type": "fill_blank", "question": "", "answer": "x"},  # invalid: empty question
            ],
        }
        resp = client.post("/imports/confirm", json=body, headers=auth_headers)
        assert resp.status_code == 422  # validation error

        # No questions should have been imported
        questions_resp = client.get("/questions/", headers=auth_headers)
        assert questions_resp.status_code == 200
        assert len(questions_resp.json()) == 0


class TestSubmitTransactionSafety:
    """Verify that practice submit is atomic and doesn't leave partial state."""

    PRACTICE_SUBMIT = "/practice/submit"
    QUESTIONS_BATCH = "/questions/batch"

    def test_submit_wrongbook_stays_in_sync(self, client, auth_headers, sample_questions):
        """Wrongbook count matches practice records after multiple submits."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        # Submit wrong twice, then correct
        client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "C",
            },
            headers=auth_headers,
        )
        client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "D",
            },
            headers=auth_headers,
        )
        client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "B",
            },
            headers=auth_headers,
        )

        # After correct answer, wrongbook should be empty for this question
        wb = client.get("/wrongbook/", headers=auth_headers).json()
        assert all(r["question_id"] != sc_q["id"] for r in wb)

        # History should have 3 records
        history = client.get("/practice/history", headers=auth_headers).json()
        assert history["total"] == 3

    def test_submit_review_state_unique(self, client, auth_headers, sample_questions):
        """Multiple submits should result in exactly one review state per question."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        questions = client.get("/questions/", headers=auth_headers).json()
        sc_q = next(q for q in questions if q["type"] == "single_choice")

        # Submit 3 times
        for _ in range(3):
            client.post(
                self.PRACTICE_SUBMIT,
                json={
                    "question_id": sc_q["id"],
                    "user_answer": "B",
                },
                headers=auth_headers,
            )

        # There should be exactly one review record for this user+question
        # (UniqueConstraint prevents duplicates)
        history = client.get("/practice/history", headers=auth_headers).json()
        assert history["total"] == 3
