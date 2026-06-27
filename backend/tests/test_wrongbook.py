"""Tests for wrongbook endpoints."""


class TestWrongBook:
    QUESTIONS_BATCH = "/questions/batch"
    PRACTICE_SUBMIT = "/practice/submit"
    WRONGBOOK_LIST = "/wrongbook/"

    def _import_and_get_question(self, client, auth_headers, sample_questions, q_type):
        """Helper: import sample questions and return the first matching question."""
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        return next(q for q in questions if q["type"] == q_type)

    def test_empty_wrongbook(self, client, auth_headers):
        resp = client.get(self.WRONGBOOK_LIST, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_wrong_answer_adds_record(self, client, auth_headers, sample_questions):
        sc_q = self._import_and_get_question(client, auth_headers, sample_questions, "single_choice")

        # Submit wrong answer
        client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "C",
            },
            headers=auth_headers,
        )

        # Check wrongbook
        resp = client.get(self.WRONGBOOK_LIST, headers=auth_headers)
        assert resp.status_code == 200
        records = resp.json()
        assert len(records) == 1
        assert records[0]["question_id"] == sc_q["id"]
        assert records[0]["wrong_count"] == 1

    def test_wrong_answer_increments_count(self, client, auth_headers, sample_questions):
        sc_q = self._import_and_get_question(client, auth_headers, sample_questions, "single_choice")

        # Submit wrong answer twice
        for _ in range(2):
            client.post(
                self.PRACTICE_SUBMIT,
                json={
                    "question_id": sc_q["id"],
                    "user_answer": "C",
                },
                headers=auth_headers,
            )

        resp = client.get(self.WRONGBOOK_LIST, headers=auth_headers)
        records = resp.json()
        assert records[0]["wrong_count"] == 2

    def test_correct_answer_clears_record(self, client, auth_headers, sample_questions):
        sc_q = self._import_and_get_question(client, auth_headers, sample_questions, "single_choice")

        # Submit wrong answer first
        client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "C",
            },
            headers=auth_headers,
        )

        # Then correct answer
        client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "B",
            },
            headers=auth_headers,
        )

        # Wrongbook should be empty
        resp = client.get(self.WRONGBOOK_LIST, headers=auth_headers)
        assert resp.json() == []

    def test_wrongbook_pagination(self, client, auth_headers, sample_questions):
        # Import and submit wrong answers to get records
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()

        # Submit wrong answers for all questions
        for q in questions:
            client.post(
                self.PRACTICE_SUBMIT,
                json={
                    "question_id": q["id"],
                    "user_answer": "wrong",
                },
                headers=auth_headers,
            )

        # Paginated query
        resp = client.get(
            self.WRONGBOOK_LIST,
            headers=auth_headers,
            params={"page": 1, "page_size": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert data["total"] == len(questions)
        assert len(data["items"]) == 2

    def test_delete_wrong_record(self, client, auth_headers, sample_questions):
        sc_q = self._import_and_get_question(client, auth_headers, sample_questions, "single_choice")

        # Submit wrong answer
        client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "C",
            },
            headers=auth_headers,
        )

        # Delete from wrongbook
        resp = client.delete(f"/wrongbook/{sc_q['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert "移除" in resp.json()["message"]

        # Verify it's gone
        resp = client.get(self.WRONGBOOK_LIST, headers=auth_headers)
        assert resp.json() == []

    def test_delete_nonexistent_record(self, client, auth_headers):
        resp = client.delete("/wrongbook/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_wrongbook_meta(self, client, auth_headers, sample_questions):
        sc_q = self._import_and_get_question(client, auth_headers, sample_questions, "single_choice")
        client.post(
            self.PRACTICE_SUBMIT,
            json={
                "question_id": sc_q["id"],
                "user_answer": "C",
            },
            headers=auth_headers,
        )

        resp = client.get("/wrongbook/meta", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "数学" in data["subjects"]
        assert "第一章" in data["chapters"]

    def test_wrongbook_meta_empty(self, client, auth_headers):
        resp = client.get("/wrongbook/meta", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["subjects"] == []
        assert data["chapters"] == []

    def test_wrongbook_filter_by_keyword(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        for q in questions:
            client.post(
                self.PRACTICE_SUBMIT,
                json={
                    "question_id": q["id"],
                    "user_answer": "wrong",
                },
                headers=auth_headers,
            )

        resp = client.get(self.WRONGBOOK_LIST, headers=auth_headers, params={"keyword": "首都"})
        records = resp.json()
        assert len(records) == 1
        assert "首都" in records[0]["question"]["question"]

    def test_wrongbook_filter_by_type(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        for q in questions:
            client.post(
                self.PRACTICE_SUBMIT,
                json={
                    "question_id": q["id"],
                    "user_answer": "wrong",
                },
                headers=auth_headers,
            )

        resp = client.get(self.WRONGBOOK_LIST, headers=auth_headers, params={"type": "single_choice"})
        records = resp.json()
        assert all(r["question"]["type"] == "single_choice" for r in records)

    def test_wrongbook_filter_by_subject(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        for q in questions:
            client.post(
                self.PRACTICE_SUBMIT,
                json={
                    "question_id": q["id"],
                    "user_answer": "wrong",
                },
                headers=auth_headers,
            )

        resp = client.get(self.WRONGBOOK_LIST, headers=auth_headers, params={"subject": "数学"})
        records = resp.json()
        assert len(records) == 1
        assert records[0]["question"]["subject"] == "数学"

    def test_wrongbook_filter_by_chapter(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        for q in questions:
            client.post(
                self.PRACTICE_SUBMIT,
                json={
                    "question_id": q["id"],
                    "user_answer": "wrong",
                },
                headers=auth_headers,
            )

        resp = client.get(self.WRONGBOOK_LIST, headers=auth_headers, params={"chapter": "第二章"})
        records = resp.json()
        assert len(records) == 2

    def test_wrongbook_paginated_with_filter(self, client, auth_headers, sample_questions):
        client.post(self.QUESTIONS_BATCH, json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/", headers=auth_headers)
        questions = resp.json()
        for q in questions:
            client.post(
                self.PRACTICE_SUBMIT,
                json={
                    "question_id": q["id"],
                    "user_answer": "wrong",
                },
                headers=auth_headers,
            )

        resp = client.get(
            self.WRONGBOOK_LIST,
            headers=auth_headers,
            params={"page": 1, "page_size": 2, "type": "single_choice"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert len(data["items"]) == 1  # only 1 single_choice question
        assert data["total"] == 1
