"""Tests for questions endpoints: batch import, list, delete, validation."""

import pytest
from pydantic import ValidationError

from backend.schemas import QuestionCreate


class TestQuestionSchema:
    """Unit tests for QuestionCreate schema (validation + normalization)."""

    def test_valid_single_choice(self):
        q = QuestionCreate(
            type="single_choice",
            question="Q?",
            options={"A": "a", "B": "b"},
            answer="A",
        )
        assert q.answer == "A"

    def test_normalize_answer_single_choice(self):
        q = QuestionCreate(
            type="single_choice",
            question="Q?",
            options={"A": "a", "B": "b"},
            answer="选项A",
        )
        assert q.answer == "A"

    def test_normalize_true_false(self):
        q = QuestionCreate(
            type="true_false",
            question="Q?",
            answer="正确",
        )
        assert q.answer == "True"

    def test_normalize_multiple_choice(self):
        q = QuestionCreate(
            type="multiple_choice",
            question="Q?",
            options={"A": "a", "B": "b", "C": "c"},
            answer="C,A",
        )
        # Should be sorted: A,C
        assert q.answer == "A,C"

    def test_empty_question_rejected(self):
        with pytest.raises(ValidationError, match="不能为空"):
            QuestionCreate(
                type="fill_blank",
                question="  ",
                answer="ans",
            )

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError, match="无效"):
            QuestionCreate(
                type="invalid",
                question="Q?",
                answer="ans",
            )

    def test_missing_options_for_choice(self):
        with pytest.raises(ValidationError, match="必须提供"):
            QuestionCreate(
                type="single_choice",
                question="Q?",
                options=None,
                answer="A",
            )

    def test_empty_answer_rejected(self):
        with pytest.raises(ValidationError, match="不能为空"):
            QuestionCreate(
                type="fill_blank",
                question="Q?",
                answer="  ",
            )


class TestQuestionsAPI:
    """Integration tests for /questions endpoints."""

    BATCH_URL = "/questions/batch"
    LIST_URL = "/questions/"

    def test_batch_import(self, client, auth_headers, sample_questions):
        resp = client.post(self.BATCH_URL, json=sample_questions, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["imported_count"] == len(sample_questions)

    def test_batch_import_empty_question_rejected(self, client, auth_headers):
        resp = client.post(
            self.BATCH_URL,
            json=[
                {"type": "fill_blank", "question": "  ", "answer": "ans"},
            ],
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_batch_import_invalid_type_rejected(self, client, auth_headers):
        resp = client.post(
            self.BATCH_URL,
            json=[
                {"type": "invalid", "question": "Q?", "answer": "ans"},
            ],
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_batch_import_missing_options(self, client, auth_headers):
        resp = client.post(
            self.BATCH_URL,
            json=[
                {"type": "single_choice", "question": "Q?", "options": None, "answer": "A"},
            ],
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_list_questions_legacy(self, client, auth_headers, sample_questions):
        client.post(self.BATCH_URL, json=sample_questions, headers=auth_headers)
        resp = client.get(self.LIST_URL, headers=auth_headers)
        assert resp.status_code == 200
        # Legacy mode returns a list
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == len(sample_questions)

    def test_list_questions_paginated(self, client, auth_headers, sample_questions):
        client.post(self.BATCH_URL, json=sample_questions, headers=auth_headers)
        resp = client.get(
            self.LIST_URL,
            headers=auth_headers,
            params={"page": 1, "page_size": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert data["total"] == len(sample_questions)
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) == 2

    def test_list_questions_filter_by_type(self, client, auth_headers, sample_questions):
        client.post(self.BATCH_URL, json=sample_questions, headers=auth_headers)
        resp = client.get(
            self.LIST_URL,
            headers=auth_headers,
            params={"type": "single_choice"},
        )
        assert resp.status_code == 200
        # Legacy mode (no page/page_size) returns list
        items = resp.json()
        assert len(items) == 1
        assert items[0]["type"] == "single_choice"

    def test_list_questions_filter_by_keyword(self, client, auth_headers, sample_questions):
        client.post(self.BATCH_URL, json=sample_questions, headers=auth_headers)
        resp = client.get(
            self.LIST_URL,
            headers=auth_headers,
            params={"keyword": "首都"},
        )
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1

    def test_delete_question(self, client, auth_headers, sample_questions):
        client.post(self.BATCH_URL, json=sample_questions, headers=auth_headers)
        # Get the first question id
        list_resp = client.get(self.LIST_URL, headers=auth_headers)
        q_id = list_resp.json()[0]["id"]

        resp = client.delete(f"/questions/{q_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["message"] == "题目已删除"

        resp = client.delete(f"/questions/{q_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthorized_access(self, client):
        resp = client.get(self.LIST_URL)
        assert resp.status_code == 401

    def test_question_meta_empty(self, client, auth_headers):
        """No questions yet, meta returns empty lists."""
        resp = client.get("/questions/meta", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["subjects"] == []
        assert data["chapters"] == []

    def test_question_meta(self, client, auth_headers, sample_questions):
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)
        resp = client.get("/questions/meta", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "数学" in data["subjects"]
        assert "地理" in data["subjects"]
        assert "常识" in data["subjects"]
        assert "第一章" in data["chapters"]
        assert "第二章" in data["chapters"]


class TestQuestionUpdate:
    """Tests for PATCH /questions/{id} and POST /questions/{id}/unpublish."""

    QUESTIONS_BATCH = "/questions/batch"

    def _create_question(self, client, auth_headers, q_type="fill_blank"):
        client.post(
            self.QUESTIONS_BATCH,
            json=[
                {
                    "type": q_type,
                    "question": "Original Q?",
                    "answer": "Original",
                }
            ],
            headers=auth_headers,
        )
        return client.get("/questions/", headers=auth_headers).json()[0]

    def test_update_subject_and_chapter(self, client, auth_headers):
        q = self._create_question(client, auth_headers)
        resp = client.patch(
            f"/questions/{q['id']}",
            json={
                "subject": "新科目",
                "chapter": "新章节",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["subject"] == "新科目"
        assert resp.json()["chapter"] == "新章节"

    def test_update_answer(self, client, auth_headers):
        q = self._create_question(client, auth_headers)
        resp = client.patch(
            f"/questions/{q['id']}",
            json={
                "answer": "NewAnswer",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["answer"] == "NewAnswer"

    def test_update_course_id(self, client, auth_headers):
        q = self._create_question(client, auth_headers)
        # Create a new course
        c_resp = client.post("/courses/", json={"name": "TargetCourse"}, headers=auth_headers)
        new_cid = c_resp.json()["id"]
        resp = client.patch(
            f"/questions/{q['id']}",
            json={
                "course_id": new_cid,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["course_id"] == new_cid

    def test_update_course_id_to_others_course_forbidden(self, client, auth_headers):
        q = self._create_question(client, auth_headers)
        # Create another user and their course
        client.post(
            "/auth/register",
            json={
                "username": "other_edit",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "other_edit", "password": "passpw"})
        other = {"Authorization": f"Bearer {r.json()['access_token']}"}
        c_resp = client.post("/courses/", json={"name": "OthersCourse"}, headers=other)
        others_cid = c_resp.json()["id"]

        resp = client.patch(
            f"/questions/{q['id']}",
            json={
                "course_id": others_cid,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_update_by_non_owner_forbidden(self, client, auth_headers):
        q = self._create_question(client, auth_headers)
        client.post(
            "/auth/register",
            json={
                "username": "non_owner",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "non_owner", "password": "passpw"})
        other = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.patch(
            f"/questions/{q['id']}",
            json={
                "subject": "hacked",
            },
            headers=other,
        )
        assert resp.status_code == 403

    def test_nonexistent_question_returns_404(self, client, auth_headers):
        resp = client.patch(
            "/questions/99999",
            json={
                "subject": "ghost",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestQuestionUnpublish:
    """Tests for POST /questions/{id}/unpublish."""

    QUESTIONS_BATCH = "/questions/batch"

    def _publish_question(self, client, auth_headers):
        client.post(
            self.QUESTIONS_BATCH,
            json=[
                {
                    "type": "fill_blank",
                    "question": "Q?",
                    "answer": "A",
                }
            ],
            headers=auth_headers,
        )
        q = client.get("/questions/", headers=auth_headers).json()[0]
        client.post(f"/questions/{q['id']}/publish", headers=auth_headers)
        return q["id"]

    def test_unpublish_makes_private(self, client, auth_headers):
        qid = self._publish_question(client, auth_headers)
        resp = client.post(f"/questions/{qid}/unpublish", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["visibility"] == "private"

    def test_unpublish_already_private_returns_400(self, client, auth_headers):
        client.post(
            self.QUESTIONS_BATCH,
            json=[
                {
                    "type": "fill_blank",
                    "question": "Private Q?",
                    "answer": "A",
                }
            ],
            headers=auth_headers,
        )
        qid = client.get("/questions/", headers=auth_headers).json()[0]["id"]
        # Already private
        resp = client.post(f"/questions/{qid}/unpublish", headers=auth_headers)
        assert resp.status_code == 400
        assert "已为私有" in resp.json()["detail"]

    def test_unpublish_by_non_owner_forbidden(self, client, auth_headers):
        qid = self._publish_question(client, auth_headers)
        client.post(
            "/auth/register",
            json={
                "username": "unpub_other",
                "password": "passpw",
                "invite_code": "dev-invite",
            },
        )
        r = client.post("/auth/login", json={"username": "unpub_other", "password": "passpw"})
        other = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.post(f"/questions/{qid}/unpublish", headers=other)
        assert resp.status_code == 403
