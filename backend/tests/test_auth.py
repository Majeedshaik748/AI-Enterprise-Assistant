def test_register_and_login(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "user@example.com", "password": "supersecret123", "full_name": "Test User"
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "user@example.com"
    assert body["role"] == "admin"  # first user bootstraps as admin

    resp = client.post("/api/v1/auth/login", json={
        "email": "user@example.com", "password": "supersecret123"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "email": "user2@example.com", "password": "supersecret123"
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "user2@example.com", "password": "wrongpassword"
    })
    assert resp.status_code == 401


def test_duplicate_registration_rejected(client):
    payload = {"email": "dup@example.com", "password": "supersecret123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 400


def test_me_requires_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_token(client, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@example.com"
