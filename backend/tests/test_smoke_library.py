"""Tests for new endpoints: /courses/mine, course questions, course practice, publish, library."""
import pytest

class TestLibrary:
    LIBRARY_PUBLIC = "/library/public"

    def test_library_public_empty(self, client, auth_headers):
        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_library_public_lists_public_courses(self, client, auth_headers):
        client.post("/courses/", json={"name": "Private", "visibility": "private"}, headers=auth_headers)
        client.post("/courses/", json={"name": "Public", "visibility": "public"}, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers)
        names = [c["name"] for c in resp.json()]
        assert "Public" in names
        assert "Private" not in names

    def test_library_public_course_questions(self, client, auth_headers, sample_questions):
        # Create a public course with questions
        resp = client.post("/courses/", json={"name": "PubCourse", "visibility": "public"}, headers=auth_headers)
        cid = resp.json()["id"]
        for q in sample_questions:
            q["course_id"] = cid
        client.post("/questions/batch", json=sample_questions, headers=auth_headers)
        # Make questions public too
        for q in client.get(f"/courses/{cid}/questions", headers=auth_headers).json():
            client.post(f"/questions/{q['id']}/publish", headers=auth_headers)

        # Other user can see them via library
        client.post("/auth/register", json={
            "username": "lib_viewer", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "lib_viewer", "password": "pass"})
        v_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(f"{self.LIBRARY_PUBLIC}/{cid}/questions", headers=v_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    def test_library_private_course_not_found(self, client, auth_headers):
        """Private courses should not be accessible via /library/public/."""
        resp = client.post("/courses/", json={"name": "Secret", "visibility": "private"}, headers=auth_headers)
        cid = resp.json()["id"]

        client.post("/auth/register", json={
            "username": "lib_spy", "password": "pass", "invite_code": "dev-invite",
        })
        r = client.post("/auth/login", json={"username": "lib_spy", "password": "pass"})
        b_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        resp = client.get(f"{self.LIBRARY_PUBLIC}/{cid}/questions", headers=b_headers)
        assert resp.status_code == 404

    def test_library_not_found(self, client, auth_headers):
        resp = client.get(f"{self.LIBRARY_PUBLIC}/99999/questions", headers=auth_headers)
        assert resp.status_code == 404

    def test_library_public_pagination(self, client, auth_headers):
        for i in range(3):
            client.post("/courses/", json={"name": f"Pub{i}", "visibility": "public"}, headers=auth_headers)
        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"page": 1, "page_size": 2})
        data = resp.json()
        assert isinstance(data, dict)
        assert data["total"] == 3
        assert len(data["items"]) == 2

    def test_library_keyword_search_name(self, client, auth_headers):
        """Keyword should match course name."""
        client.post("/courses/", json={"name": "高等数学", "visibility": "public"}, headers=auth_headers)
        client.post("/courses/", json={"name": "大学英语", "visibility": "public"}, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"keyword": "数学"})
        items = resp.json()
        assert len(items) == 1
        assert items[0]["name"] == "高等数学"

    def test_library_keyword_search_description(self, client, auth_headers):
        """Keyword should match course description."""
        client.post("/courses/", json={
            "name": "数学习题集",
            "description": "涵盖初中数学全部知识点",
            "visibility": "public",
        }, headers=auth_headers)
        client.post("/courses/", json={
            "name": "英语题库",
            "description": "四级考试真题",
            "visibility": "public",
        }, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"keyword": "初中"})
        items = resp.json()
        assert len(items) == 1
        assert items[0]["name"] == "数学习题集"

    def test_library_keyword_search_subject(self, client, auth_headers):
        """Keyword should match subject field."""
        client.post("/courses/", json={
            "name": "C1", "subject": "物理", "visibility": "public",
        }, headers=auth_headers)
        client.post("/courses/", json={
            "name": "C2", "subject": "化学", "visibility": "public",
        }, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"keyword": "物理"})
        items = resp.json()
        assert len(items) == 1
        assert items[0]["subject"] == "物理"

    def test_library_subject_filter_exact(self, client, auth_headers):
        """Subject param should do exact match."""
        client.post("/courses/", json={
            "name": "C1", "subject": "数学", "visibility": "public",
        }, headers=auth_headers)
        client.post("/courses/", json={
            "name": "C2", "subject": "物理", "visibility": "public",
        }, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"subject": "数学"})
        items = resp.json()
        assert len(items) == 1
        assert items[0]["subject"] == "数学"

    def test_library_keyword_no_match(self, client, auth_headers):
        """Keyword with no matches returns empty."""
        client.post("/courses/", json={"name": "数学", "visibility": "public"}, headers=auth_headers)
        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"keyword": "不存在的"})
        assert resp.json() == []

    def test_library_keyword_does_not_match_private(self, client, auth_headers):
        """Keyword should not return private courses."""
        client.post("/courses/", json={"name": "私有数学", "visibility": "private"}, headers=auth_headers)
        client.post("/courses/", json={"name": "公开数学", "visibility": "public"}, headers=auth_headers)

        resp = client.get(self.LIBRARY_PUBLIC, headers=auth_headers, params={"keyword": "数学"})
        names = [c["name"] for c in resp.json()]
        assert "公开数学" in names
        assert "私有数学" not in names
