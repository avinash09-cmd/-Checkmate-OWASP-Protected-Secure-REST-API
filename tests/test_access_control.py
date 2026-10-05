from tests.conftest import register_and_login


def test_user_cannot_access_another_users_task(client):
    headers_a = register_and_login(client, "alice@example.com")
    headers_b = register_and_login(client, "bob@example.com")

    r = client.post("/tasks", json={"title": "Alice's secret task"}, headers=headers_a)
    task_id = r.json()["id"]

    # Bob tries to read Alice's task directly by ID
    r = client.get(f"/tasks/{task_id}", headers=headers_b)
    assert r.status_code == 404  # not 403 — existence isn't confirmed either

    # Bob tries to delete it
    r = client.delete(f"/tasks/{task_id}", headers=headers_b)
    assert r.status_code == 404

    # Alice can still access her own task
    r = client.get(f"/tasks/{task_id}", headers=headers_a)
    assert r.status_code == 200


def test_normal_user_cannot_access_admin_routes(client):
    # second registered user is a normal 'user', not admin (first user becomes admin)
    register_and_login(client, "firstadmin@example.com")
    headers = register_and_login(client, "normal@example.com")

    r = client.get("/admin/users", headers=headers)
    assert r.status_code == 403

    r = client.get("/admin/audit-logs", headers=headers)
    assert r.status_code == 403


def test_first_registered_user_is_admin(client):
    headers = register_and_login(client, "firstuser@example.com")
    r = client.get("/admin/users", headers=headers)
    assert r.status_code == 200
