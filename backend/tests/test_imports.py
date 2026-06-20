"""Tests for imports endpoints: file upload, size limits, AI auto import."""
import io
from unittest.mock import patch

import pytest


def _make_docx_bytes(text: str = "Test content paragraph.\nSecond paragraph.") -> bytes:
    """Create a minimal .docx file in-memory."""
    from docx import Document
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


class TestFileImport:
    FILE_UPLOAD = "/imports/file"
    FILE_AUTO = "/imports/file/auto"
    QUESTIONS_BATCH = "/questions/batch"

    def test_upload_docx(self, client, auth_headers):
        content = _make_docx_bytes("这是测试文本。\n第二行内容。")
        resp = client.post(
            self.FILE_UPLOAD,
            headers=auth_headers,
            files={"file": ("test.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "text" in data
        assert "这是测试文本" in data["text"]

    def test_upload_docx_returns_suggested_course_name(self, client, auth_headers):
        """File upload should return suggested_course_name derived from the filename."""
        content = _make_docx_bytes("Some content.")
        resp = client.post(
            self.FILE_UPLOAD,
            headers=auth_headers,
            files={"file": ("java复习题.docx", content,
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["suggested_course_name"] == "java复习题"

    def test_upload_unsupported_format(self, client, auth_headers):
        resp = client.post(
            self.FILE_UPLOAD,
            headers=auth_headers,
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 400
        assert "不支持" in resp.json()["detail"]

    def test_upload_file_too_large(self, client, auth_headers):
        # Create content slightly larger than 10MB limit
        large_content = b"x" * (11 * 1024 * 1024)
        resp = client.post(
            self.FILE_UPLOAD,
            headers=auth_headers,
            files={"file": ("large.docx", large_content,
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp.status_code == 413
        assert "超过" in resp.json()["detail"]

    def test_unauthorized(self, client):
        resp = client.post(self.FILE_UPLOAD, files={"file": ("test.docx", b"x", "application/octet-stream")})
        assert resp.status_code == 401

    @patch("backend.routers.imports.OPENAI_API_KEY", "")
    def test_auto_no_openai_key(self, client, auth_headers):
        """Without OPENAI_API_KEY set, /file/auto should return 400 with clear message."""
        content = _make_docx_bytes("Test question content.")
        resp = client.post(
            self.FILE_AUTO,
            headers=auth_headers,
            files={"file": ("test.docx", content,
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert "OPENAI_API_KEY" in detail


class TestDeriveCourseName:
    """Tests for the derive_course_name_from_filename utility."""

    def test_normal_file(self):
        from backend.crud import derive_course_name_from_filename
        assert derive_course_name_from_filename("java复习题.docx") == "java复习题"

    def test_pptx_file(self):
        from backend.crud import derive_course_name_from_filename
        assert derive_course_name_from_filename("期末考试题.pptx") == "期末考试题"

    def test_whitespace_collapsed(self):
        from backend.crud import derive_course_name_from_filename
        assert derive_course_name_from_filename("  期末  考试 题.pptx ") == "期末 考试 题"

    def test_empty_filename(self):
        from backend.crud import derive_course_name_from_filename
        assert derive_course_name_from_filename("") == "未分类题库"

    def test_none_filename(self):
        from backend.crud import derive_course_name_from_filename
        assert derive_course_name_from_filename(None) == "未分类题库"

    def test_illegal_chars_stripped(self):
        from backend.crud import derive_course_name_from_filename
        result = derive_course_name_from_filename("math: test? <foo>.docx")
        assert "math test foo" == result or "math  test  foo" == result

    def test_truncate_long(self):
        from backend.crud import derive_course_name_from_filename
        long_name = "a" * 200 + ".docx"
        result = derive_course_name_from_filename(long_name)
        assert len(result) == 80


class TestCourseNameInBatchImport:
    """Test that /questions/batch respects course_name query param."""

    def test_batch_with_course_name_creates_new(self, client, auth_headers):
        """batch?course_name=Java复习题 should create that bank."""
        resp = client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Q?", "answer": "A",
        }], headers=auth_headers, params={"course_name": "Java复习题"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["course_name"] == "Java复习题"
        assert data["course_id"] is not None

    def test_batch_with_course_name_reuses_existing(self, client, auth_headers):
        """Second batch with same course_name should reuse the bank."""
        client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Q1?", "answer": "A",
        }], headers=auth_headers, params={"course_name": "Reused"})
        resp2 = client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Q2?", "answer": "B",
        }], headers=auth_headers, params={"course_name": "Reused"})
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["course_name"] == "Reused"

        # Should only be one "Reused" bank
        courses = client.get("/courses/mine", headers=auth_headers).json()
        matching = [c for c in courses if c["name"] == "Reused"]
        assert len(matching) == 1

    def test_batch_course_id_overrides_course_name(self, client, auth_headers):
        """course_id > 0 should take priority over course_name."""
        # Create a named course
        bank = client.post("/courses/", json={"name": "ExistingCourse"}, headers=auth_headers).json()
        cid = bank["id"]

        # Use course_id, passing a different course_name
        resp = client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Q?", "answer": "A",
        }], headers=auth_headers, params={"course_id": cid, "course_name": "Ignored"})
        assert resp.status_code == 200
        assert resp.json()["course_name"] == "ExistingCourse"

    def test_batch_without_course_name_fallsback_uncategorized(self, client, auth_headers):
        """No course_id and no course_name → fallback to 未分类题库."""
        resp = client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Q?", "answer": "A",
        }], headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["course_name"] == "未分类题库"


class TestFileAutoCourseName:
    """Tests for /imports/file/auto course_name parameter."""

    FILE_AUTO = "/imports/file/auto"

    def _mock_openai_response(self):
        """Return a mock OpenAI response that returns a valid questions JSON."""
        import json
        mock = patch("openai.OpenAI")
        mock_client = mock.start()
        instance = mock_client.return_value
        instance.chat.completions.create.return_value.choices = [
            type("obj", (), {"message": type("obj", (), {"content": json.dumps({
                "questions": [{"type": "fill_blank", "question": "Mock Q?", "answer": "A"}]
            })})()})()
        ]
        return mock

    def _make_docx(self):
        return _make_docx_bytes("Some content.")

    @patch("backend.routers.imports.OPENAI_API_KEY", "sk-test")
    def test_auto_course_name_creates_new(self, client, auth_headers):
        """course_name=Java复习题 should create that bank."""
        mock = self._mock_openai_response()
        try:
            content = self._make_docx()
            resp = client.post(
                self.FILE_AUTO,
                headers=auth_headers,
                files={"file": ("ignored.docx", content,
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                params={"course_name": "Java复习题"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["course_name"] == "Java复习题"
            assert data["course_id"] is not None
        finally:
            mock.stop()

    @patch("backend.routers.imports.OPENAI_API_KEY", "sk-test")
    def test_auto_course_id_overrides_course_name(self, client, auth_headers):
        """course_id > 0 should take priority even when course_name is given."""
        # Create a course first
        bank = client.post("/courses/", json={"name": "ExistingCourse"}, headers=auth_headers).json()
        cid = bank["id"]

        mock = self._mock_openai_response()
        try:
            content = self._make_docx()
            resp = client.post(
                self.FILE_AUTO,
                headers=auth_headers,
                files={"file": ("ignored.docx", content,
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                params={"course_id": cid, "course_name": "IgnoredName"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["course_name"] == "ExistingCourse"
        finally:
            mock.stop()

    @patch("backend.routers.imports.OPENAI_API_KEY", "sk-test")
    def test_auto_derives_from_filename_when_no_course_name(self, client, auth_headers):
        """With no course_name, should derive from filename."""
        mock = self._mock_openai_response()
        try:
            content = self._make_docx()
            resp = client.post(
                self.FILE_AUTO,
                headers=auth_headers,
                files={"file": ("java复习题.docx", content,
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["course_name"] == "java复习题"
        finally:
            mock.stop()

    @patch("backend.routers.imports.OPENAI_API_KEY", "sk-test")
    def test_auto_user_isolation_same_name(self, client, auth_headers):
        """Different users with same course_name should get separate banks."""
        alice = auth_headers
        # Register bob
        client.post("/auth/register", json={
            "username": "bob_auto_cn", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "bob_auto_cn", "password": "pass"})
        bob = {"Authorization": f"Bearer {r.json()['access_token']}"}

        mock = self._mock_openai_response()
        try:
            content = self._make_docx()

            r1 = client.post(
                self.FILE_AUTO, headers=alice,
                files={"file": ("ignored.docx", content, "application/octet-stream")},
                params={"course_name": "SharedName"},
            )
            r2 = client.post(
                self.FILE_AUTO, headers=bob,
                files={"file": ("ignored.docx", content, "application/octet-stream")},
                params={"course_name": "SharedName"},
            )
            assert r1.status_code == 200
            assert r2.status_code == 200
            assert r1.json()["course_id"] != r2.json()["course_id"]
        finally:
            mock.stop()


class TestCourseNameUserIsolation:
    """Different users should have separate banks even with the same name."""

    def _auth(self, client, username):
        client.post("/auth/register", json={
            "username": username, "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": username, "password": "pass"})
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def test_same_name_different_users(self, client):
        alice = self._auth(client, "alice_cn")
        bob = self._auth(client, "bob_cn")

        # Alice creates a course via batch import
        r = client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Alice Q?", "answer": "A",
        }], headers=alice, params={"course_name": "MyCourse"})
        alice_cid = r.json()["course_id"]

        # Bob does the same — should create a separate bank
        r = client.post("/questions/batch", json=[{
            "type": "fill_blank", "question": "Bob Q?", "answer": "B",
        }], headers=bob, params={"course_name": "MyCourse"})
        bob_cid = r.json()["course_id"]

        # Different course IDs
        assert alice_cid != bob_cid

        # Alice sees 1 course, Bob sees 1 course (their own)
        assert len(client.get("/courses/mine", headers=alice).json()) == 1
        assert len(client.get("/courses/mine", headers=bob).json()) == 1
