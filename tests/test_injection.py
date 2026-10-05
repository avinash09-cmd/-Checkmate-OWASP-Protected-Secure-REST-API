from tests.conftest import register_and_login


def test_sql_injection_string_in_login_is_handled_safely(client):
    r = client.post(
        "/auth/login",
        json={"email": "' OR '1'='1", "password": "' OR '1'='1"},
    )
    # Should fail validation (not a valid email) or auth, never 500, never log in
    assert r.status_code in (401, 422)


def test_sql_injection_string_in_task_title_is_stored_safely(client):
    headers = register_and_login(client, "injtest@example.com")
    payload = {"title": "Robert'); DROP TABLE tasks;--"}
    r = client.post("/tasks", json=payload, headers=headers)
    assert r.status_code == 201
    # ORM parameterization means this is stored as inert text, not executed
    assert r.json()["title"] == payload["title"]

    # Table still exists and still works normally afterward
    r = client.get("/tasks", headers=headers)
    assert r.status_code == 200


def test_oversized_title_rejected(client):
    headers = register_and_login(client, "oversize@example.com")
    r = client.post("/tasks", json={"title": "x" * 500}, headers=headers)
    assert r.status_code == 422


def test_empty_title_rejected(client):
    headers = register_and_login(client, "emptytitle@example.com")
    r = client.post("/tasks", json={"title": "   "}, headers=headers)
    assert r.status_code == 422
