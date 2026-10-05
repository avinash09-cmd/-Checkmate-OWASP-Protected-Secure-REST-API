from tests.conftest import register_and_login


def test_register_and_login(client):
    r = client.post("/auth/register", json={"email": "a@example.com", "password": "StrongPass123"})
    assert r.status_code == 201
    assert "password_hash" not in r.json()  # password hash must never be returned

    r = client.post("/auth/login", json={"email": "a@example.com", "password": "StrongPass123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password_returns_generic_error(client):
    client.post("/auth/register", json={"email": "b@example.com", "password": "StrongPass123"})
    r = client.post("/auth/login", json={"email": "b@example.com", "password": "WrongPassword1"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid email or password"


def test_login_nonexistent_user_same_generic_error(client):
    r = client.post("/auth/login", json={"email": "nouser@example.com", "password": "WhateverPass1"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid email or password"


def test_weak_password_rejected(client):
    r = client.post("/auth/register", json={"email": "c@example.com", "password": "weak"})
    assert r.status_code == 422


def test_unknown_field_rejected(client):
    r = client.post(
        "/auth/register",
        json={"email": "d@example.com", "password": "StrongPass123", "role": "admin"},
    )
    assert r.status_code == 422  # extra='forbid' blocks privilege-escalation-by-extra-field


def test_protected_route_requires_token(client):
    r = client.get("/tasks")
    assert r.status_code == 401
