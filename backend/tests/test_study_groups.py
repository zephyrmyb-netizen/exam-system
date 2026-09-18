"""Group boundaries and late-join access must agree with course permissions."""

from backend import models


def test_group_courses_are_scoped_and_late_joiners_can_read(client, auth_headers, auth_headers_other, db_session):
    group_a = client.post("/study-groups/", headers=auth_headers, json={"name": "A"}).json()
    group_b = client.post("/study-groups/", headers=auth_headers, json={"name": "B"}).json()
    course = client.post("/courses/", headers=auth_headers, json={"name": "Only A"}).json()
    path = f"/study-groups/{group_a['id']}/courses/{course['id']}"
    assert client.post(path, headers=auth_headers).status_code == 200
    assert client.post(path, headers=auth_headers).status_code == 200
    assert db_session.query(models.StudyGroupCourse).count() == 1
    assert client.get(f"/study-groups/{group_b['id']}/resources", headers=auth_headers).json()["courses"] == []
    assert client.get(f"/study-groups/{group_a['id']}/resources", headers=auth_headers_other).status_code == 404

    join_path = f"/study-groups/join/{group_a['invite_code']}"
    assert client.post(join_path, headers=auth_headers_other).status_code == 200
    assert client.post(join_path, headers=auth_headers_other).status_code == 200
    result = client.get(f"/study-groups/{group_a['id']}/resources", headers=auth_headers_other).json()
    assert result["courses"] == [{"id": course["id"], "name": "Only A", "question_count": 0}]
    assert client.get(f"/courses/{course['id']}", headers=auth_headers_other).status_code == 200
    assert client.post(path, headers=auth_headers_other).status_code == 403
    assert db_session.query(models.Collaboration).count() == 1
    mine = client.get("/study-groups/mine", headers=auth_headers).json()
    assert {row["id"]: row["member_count"] for row in mine} == {group_a["id"]: 2, group_b["id"]: 1}


def test_legacy_collaborations_do_not_infer_group_resources(client, auth_headers, auth_headers_other, db_session):
    group = client.post("/study-groups/", headers=auth_headers, json={"name": "Unrelated"}).json()
    course = client.post("/courses/", headers=auth_headers, json={"name": "Legacy"}).json()
    other = client.get("/auth/me", headers=auth_headers_other).json()
    db_session.add(models.Collaboration(course_id=course["id"], user_id=other["id"], invited_by=group["owner_id"]))
    db_session.commit()
    assert client.get(f"/study-groups/{group['id']}/resources", headers=auth_headers).json()["courses"] == []


def test_blank_group_rejected(client, auth_headers):
    assert client.post("/study-groups/", headers=auth_headers, json={"name": "   "}).status_code == 422


def test_import_original_is_not_a_public_static_file(client, tmp_path, monkeypatch):
    from backend import main

    original = tmp_path / "private.docx"
    original.write_bytes(b"private exam content")
    assert not any(getattr(route, "path", "") == "/uploads" for route in main.app.routes)
    assert client.get("/uploads/import_tasks/private.docx").status_code == 404
