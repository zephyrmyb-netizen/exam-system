"""Tests for questions endpoints: batch import, list, delete, validation."""
import pytest
from pydantic import ValidationError
from backend.schemas import QuestionCreate
from backend.utils import normalize_answer


class TestQuestionSchema:
    """Unit tests for QuestionCreate schema (validation + normalization)."""

    def test_valid_single_choice(self):
        q = QuestionCreate(
            type="single_choice", question="Q?",
            options={"A": "a", "B": "b"}, answer="A",
        )
        assert q.answer == "A"

    def test_normalize_answer_single_choice(self):
        q = QuestionCreate(
            type="single_choice", question="Q?",
            options={"A": "a", "B": "b"}, answer="选项A",
        )
        assert q.answer == "A"

    def test_normalize_true_false(self):
        q = QuestionCreate(
            type="true_false", question="Q?", answer="正确",
        )
        assert q.answer == "True"

    def test_normalize_multiple_choice(self):
        q = QuestionCreate(
            type="multiple_choice", question="Q?",
            options={"A": "a", "B": "b", "C": "c"}, answer="C,A",
        )
        # Should be sorted: A,C
        assert q.answer == "A,C"

    def test_empty_question_rejected(self):
        with pytest.raises(ValidationError, match="不能为空"):
            QuestionCreate(
                type="fill_blank", question="  ", answer="ans",
            )

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError, match="无效"):
            QuestionCreate(
                type="invalid", question="Q?", answer="ans",
            )

    def test_missing_options_for_choice(self):
        with pytest.raises(ValidationError, match="必须提供"):
            QuestionCreate(
                type="single_choice", question="Q?", options=None, answer="A",
            )

    def test_empty_answer_rejected(self):
        with pytest.raises(ValidationError, match="不能为空"):
            QuestionCreate(
                type="fill_blank", question="Q?", answer="  ",
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
        resp = client.post(self.BATCH_URL, json=[
            {"type": "fill_blank", "question": "  ", "answer": "ans"},
        ], headers=auth_headers)
        assert resp.status_code == 422

    def test_batch_import_invalid_type_rejected(self, client, auth_headers):
        resp = client.post(self.BATCH_URL, json=[
            {"type": "invalid", "question": "Q?", "answer": "ans"},
        ], headers=auth_headers)
        assert resp.status_code == 422

    def test_batch_import_missing_options(self, client, auth_headers):
        resp = client.post(self.BATCH_URL, json=[
            {"type": "single_choice", "question": "Q?", "options": None, "answer": "A"},
        ], headers=auth_headers)
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
