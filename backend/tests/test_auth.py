"""Tests for auth endpoints: register, login, me."""
import pytest


class TestAuth:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "username": "newuser",
            "password": "secret",
            "invite_code": "dev-invite",
        })
        assert resp.status_code == 201
        assert resp.json()["message"] == "注册成功"

    def test_register_empty_invite_code(self, client):
        resp = client.post("/auth/register", json={
            "username": "newuser",
            "password": "secret",
            "invite_code": "",
        })
        assert resp.status_code == 400
        assert "邀请码" in resp.json()["detail"]

    def test_register_wrong_invite_code(self, client):
        resp = client.post("/auth/register", json={
            "username": "newuser",
            "password": "secret",
            "invite_code": "wrong-code",
        })
        assert resp.status_code == 400
        assert "邀请码" in resp.json()["detail"]

    def test_register_duplicate_username(self, client):
        client.post("/auth/register", json={
            "username": "dupuser",
            "password": "secret",
            "invite_code": "dev-invite",
        })
        resp = client.post("/auth/register", json={
            "username": "dupuser",
            "password": "secret",
            "invite_code": "dev-invite",
        })
        assert resp.status_code == 400
        assert "已存在" in resp.json()["detail"]

    def test_login_success(self, client):
        client.post("/auth/register", json={
            "username": "loginuser",
            "password": "mypassword",
            "invite_code": "dev-invite",
        })
        resp = client.post("/auth/login", json={
            "username": "loginuser",
            "password": "mypassword",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        client.post("/auth/register", json={
            "username": "user1",
            "password": "correctpw",
            "invite_code": "dev-invite",
        })
        resp = client.post("/auth/login", json={
            "username": "user1",
            "password": "wrongpw",
        })
        assert resp.status_code == 401
        assert "错误" in resp.json()["detail"]

    def test_me(self, client, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    def test_me_unauthorized(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401
