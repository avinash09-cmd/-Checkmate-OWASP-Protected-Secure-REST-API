import base64
import json

from app.core.config import settings


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def test_tampered_token_rejected(client):
    client.post("/auth/register", json={"email": "tok@example.com", "password": "StrongPass123"})
    login = client.post("/auth/login", json={"email": "tok@example.com", "password": "StrongPass123"})
    token = login.json()["access_token"]

    tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
    r = client.get("/tasks", headers={"Authorization": f"Bearer {tampered}"})
    assert r.status_code == 401


def test_alg_none_token_rejected(client):
    # Hand-craft a classic "alg: none" JWT attack. python-jose refuses to even
    # *create* a none-alg token (it's not in its supported algorithm list),
    # which is itself a good sign — so we build the raw token bytes ourselves
    # to prove the server-side decoder also refuses to accept one.
    header = _b64url(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({"sub": "fake-user-id", "role": "admin"}).encode())
    forged = f"{header}.{payload}."  # empty signature, as the "none" alg attack requires

    r = client.get("/tasks", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


def test_response_never_exposes_password_hash(client):
    r = client.post("/auth/register", json={"email": "nohash@example.com", "password": "StrongPass123"})
    assert "password_hash" not in r.text
    assert "password" not in r.json()


def test_repeated_failed_logins_eventually_rate_limited(client):
    client.post("/auth/register", json={"email": "ratelimit@example.com", "password": "StrongPass123"})
    statuses = []
    for _ in range(10):
        r = client.post(
            "/auth/login", json={"email": "ratelimit@example.com", "password": "WrongPassword1"}
        )
        statuses.append(r.status_code)
    # After LOGIN_RATE_LIMIT (default 5/minute) failed attempts, we expect 429s to show up
    assert 429 in statuses
