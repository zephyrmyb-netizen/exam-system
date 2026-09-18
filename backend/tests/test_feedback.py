from backend import models


def test_feedback_requires_login(client):
    response = client.post("/feedback/", json={"category": "bug", "content": "无法登录账号"})

    assert response.status_code == 401


def test_authenticated_user_can_submit_persistent_feedback(client, auth_headers, db_session):
    response = client.post(
        "/feedback/",
        headers=auth_headers,
        json={"category": "suggestion", "content": "希望增加帮助中心", "contact": "user@example.com"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] > 0
    assert payload["category"] == "suggestion"

    stored = db_session.query(models.FeedbackEntry).filter_by(id=payload["id"]).one()
    assert stored.content == "希望增加帮助中心"
    assert stored.contact == "user@example.com"
