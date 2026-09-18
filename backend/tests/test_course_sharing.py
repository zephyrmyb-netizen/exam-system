"""Private course links must create independent copies, not grant direct access."""


def test_private_course_share_copies_questions_for_recipient(client, auth_headers, auth_headers_other):
    created = client.post(
        "/courses/",
        headers=auth_headers,
        json={"name": "Private source", "description": "Only by link", "subject": "Math"},
    )
    assert created.status_code == 201
    course_id = created.json()["id"]
    mine = client.get("/courses/mine", headers=auth_headers)
    assert mine.status_code == 200
    assert mine.json()[0]["share_token"]
    question = client.post(
        "/questions/",
        headers=auth_headers,
        json={
            "course_id": course_id,
            "type": "single_choice",
            "question": "2 + 2 = ?",
            "options": {"A": "3", "B": "4"},
            "answer": "B",
            "analysis": "basic arithmetic",
        },
    )
    assert question.status_code == 201

    # The normal private detail path remains inaccessible to the recipient.
    assert client.get(f"/courses/{course_id}", headers=auth_headers_other).status_code == 404

    link = client.post(f"/courses/{course_id}/share-link", headers=auth_headers)
    assert link.status_code == 200
    token = link.json()["token"]
    assert len(token) >= 32
    assert token == mine.json()[0]["share_token"]

    preview = client.get(f"/courses/share/{token}", headers=auth_headers_other)
    assert preview.status_code == 200
    assert preview.json() == {
        "name": "Private source",
        "description": "Only by link",
        "subject": "Math",
        "question_count": 1,
    }

    copied = client.post(f"/courses/share/{token}/copy", headers=auth_headers_other)
    assert copied.status_code == 201
    copied_course = copied.json()
    assert copied_course["owner_id"] != created.json()["owner_id"]
    assert copied_course["visibility"] == "private"
    assert copied_course["question_count"] == 1

    copied_questions = client.get(f"/courses/{copied_course['id']}/questions", headers=auth_headers_other)
    assert copied_questions.status_code == 200
    assert copied_questions.json()[0]["question"] == "2 + 2 = ?"


def test_only_owner_can_create_private_share_link(client, auth_headers, auth_headers_other):
    created = client.post("/courses/", headers=auth_headers, json={"name": "Owner only"})
    response = client.post(f"/courses/{created.json()['id']}/share-link", headers=auth_headers_other)
    assert response.status_code == 403
