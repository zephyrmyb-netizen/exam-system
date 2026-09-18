"""Per-IP rate limiting on unauthenticated auth endpoints (login/register/guest)."""

import pytest

from backend.main import app
from backend.ratelimit import MemoryRateLimiter
from backend.routers.auth import rate_limiter as auth_rl_dep


@pytest.fixture()
def strict_auth_limiter():
    """Install a real in-process limiter, replacing the default no-op override."""
    limiter = MemoryRateLimiter()
    app.dependency_overrides[auth_rl_dep] = lambda: limiter
    yield limiter
    app.dependency_overrides.pop(auth_rl_dep, None)


def _login(client, ip):
    return client.post(
        "/auth/login",
        json={"username": "nobody", "password": "wrong"},
        headers={"X-Forwarded-For": ip},
    )


def test_login_blocked_after_burst_from_one_ip(client, strict_auth_limiter, monkeypatch):
    monkeypatch.setattr("backend.routers.auth.AUTH_RATE_LIMIT_PER_MINUTE", 3)

    for _ in range(3):
        assert _login(client, "203.0.113.9").status_code == 401

    blocked = _login(client, "203.0.113.9")
    assert blocked.status_code == 429
    assert "尝试过于频繁" in blocked.json()["detail"]


def test_auth_limit_scopes_by_ip(client, strict_auth_limiter, monkeypatch):
    monkeypatch.setattr("backend.routers.auth.AUTH_RATE_LIMIT_PER_MINUTE", 2)

    assert _login(client, "203.0.113.9").status_code == 401
    assert _login(client, "203.0.113.9").status_code == 401
    assert _login(client, "203.0.113.9").status_code == 429

    # A different client is not affected by the first IP's bucket.
    assert _login(client, "198.51.100.7").status_code == 401


def test_register_and_login_share_the_ip_bucket(client, strict_auth_limiter, monkeypatch):
    monkeypatch.setattr("backend.routers.auth.AUTH_RATE_LIMIT_PER_MINUTE", 2)

    for _ in range(2):
        response = client.post(
            "/auth/register",
            json={"username": "someone", "password": "password123", "invite_code": "wrong-code"},
            headers={"X-Forwarded-For": "203.0.113.9"},
        )
        assert response.status_code == 400  # wrong invite code, but still counted

    assert _login(client, "203.0.113.9").status_code == 429


def test_cf_connecting_ip_takes_priority_over_forwarded_for(client, strict_auth_limiter, monkeypatch):
    monkeypatch.setattr("backend.routers.auth.AUTH_RATE_LIMIT_PER_MINUTE", 1)

    assert (
        client.post(
            "/auth/login",
            json={"username": "nobody", "password": "wrong"},
            headers={"X-Forwarded-For": "203.0.113.9", "CF-Connecting-IP": "192.0.2.4"},
        ).status_code
        == 401
    )
    # Same CF client IP, different X-Forwarded-For: the CF header wins, so this
    # request hits the same bucket and is blocked.
    assert (
        client.post(
            "/auth/login",
            json={"username": "nobody", "password": "wrong"},
            headers={"X-Forwarded-For": "198.51.100.7", "CF-Connecting-IP": "192.0.2.4"},
        ).status_code
        == 429
    )
