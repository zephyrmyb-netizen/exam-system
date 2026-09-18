"""Tests for auth endpoints: register, login, me."""


class TestAuth:
    def test_register_success(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "password": "secret",
                "invite_code": "dev-invite",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["message"] == "注册成功"

    def test_register_empty_invite_code(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "password": "secret",
                "invite_code": "",
            },
        )
        # 空邀请码现在由 Pydantic schema 层（min_length=1）拦截，返回 422
        assert resp.status_code == 422

    def test_register_wrong_invite_code(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "password": "secret",
                "invite_code": "wrong-code",
            },
        )
        assert resp.status_code == 400
        assert "邀请码" in resp.json()["detail"]

    def test_register_duplicate_username(self, client):
        client.post(
            "/auth/register",
            json={
                "username": "dupuser",
                "password": "secret",
                "invite_code": "dev-invite",
            },
        )
        resp = client.post(
            "/auth/register",
            json={
                "username": "dupuser",
                "password": "secret",
                "invite_code": "dev-invite",
            },
        )
        assert resp.status_code == 400
        assert "已存在" in resp.json()["detail"]

    def test_login_success(self, client):
        client.post(
            "/auth/register",
            json={
                "username": "loginuser",
                "password": "mypassword",
                "invite_code": "dev-invite",
            },
        )
        resp = client.post(
            "/auth/login",
            json={
                "username": "loginuser",
                "password": "mypassword",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "token" in data
        assert data["token_type"] == "bearer"
        assert "xuexibao_access" in resp.headers["set-cookie"]
        assert "HttpOnly" in resp.headers["set-cookie"]
        assert "SameSite=lax" in resp.headers["set-cookie"]

    def test_cookie_session_can_access_profile_and_logout(self, client):
        client.post(
            "/auth/register",
            json={
                "username": "cookieuser",
                "password": "mypassword",
                "invite_code": "dev-invite",
            },
        )
        client.post("/auth/login", json={"username": "cookieuser", "password": "mypassword"})

        assert client.get("/auth/me").json()["username"] == "cookieuser"

        logout = client.post("/auth/logout")
        assert logout.status_code == 204
        assert "xuexibao_access" in logout.headers["set-cookie"]
        assert client.get("/auth/me").status_code == 401

    def test_login_wrong_password(self, client):
        client.post(
            "/auth/register",
            json={
                "username": "user1",
                "password": "correctpw",
                "invite_code": "dev-invite",
            },
        )
        resp = client.post(
            "/auth/login",
            json={
                "username": "user1",
                "password": "wrongpw",
            },
        )
        assert resp.status_code == 401
        assert "错误" in resp.json()["detail"]

    def test_me(self, client, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"
        assert resp.json()["role"] == "student"
        assert resp.json()["permissions"] == []

    def test_me_unauthorized(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_register_missing_username(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "password": "secret",
                "invite_code": "dev-invite",
            },
        )
        assert resp.status_code == 422

    def test_register_missing_password(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "username": "nopw",
                "invite_code": "dev-invite",
            },
        )
        assert resp.status_code == 422

    def test_register_whitespace_username(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "username": "   ",
                "password": "secret",
                "invite_code": "dev-invite",
            },
        )
        # 纯空格用户名不匹配 ^[A-Za-z0-9_]+$ 模式，由 schema 层拦截返回 422
        assert resp.status_code == 422

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/auth/login",
            json={
                "username": "doesnotexist",
                "password": "whatever",
            },
        )
        assert resp.status_code == 401

    def test_guest_trial_is_testing_only(self, client):
        assert client.post("/auth/guest", json={"nickname": "visitor"}).status_code == 404

    def test_guest_trial_generates_a_name_when_no_nickname_is_sent(self, client, monkeypatch):
        from backend.routers import auth

        monkeypatch.setattr(auth, "APP_ENV", "testing")

        response = client.post("/auth/guest", json={})

        assert response.status_code == 201
        profile = client.get("/auth/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"})
        assert profile.status_code == 200
        assert profile.json()["is_guest"] is True
        assert profile.json()["display_name"].startswith("游客")

    def test_guest_trial_is_isolated_and_can_clear_own_data(self, client, monkeypatch):
        from backend.routers import auth

        monkeypatch.setattr(auth, "APP_ENV", "testing")

        first = client.post("/auth/guest", json={"nickname": "first visitor"})
        second = client.post("/auth/guest", json={"nickname": "second visitor"})
        assert first.status_code == 201
        assert second.status_code == 201

        first_headers = {"Authorization": f"Bearer {first.json()['access_token']}"}
        second_headers = {"Authorization": f"Bearer {second.json()['access_token']}"}
        first_profile = client.get("/auth/me", headers=first_headers)
        second_profile = client.get("/auth/me", headers=second_headers)
        assert first_profile.json()["is_guest"] is True
        assert first_profile.json()["display_name"] == "first visitor"
        assert first_profile.json()["id"] != second_profile.json()["id"]

        assert client.delete("/auth/guest/me", headers=first_headers).status_code == 204
        assert client.get("/auth/me", headers=first_headers).status_code == 401
        assert client.get("/auth/me", headers=second_headers).status_code == 200
