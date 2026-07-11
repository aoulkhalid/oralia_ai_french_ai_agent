def test_register_creates_user(client):
    resp = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["niveau_cecrl"] == "A1"
    assert data["role"] == "student"
    assert data["plan"] == "free"
    assert "hashed_password" not in data  # jamais exposé


def test_register_rejects_duplicate_email(client):
    payload = {"email": "bob@example.com", "password": "password123"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400


def test_register_rejects_weak_password(client):
    resp = client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": "onlyletters"},
    )
    assert resp.status_code == 422  # pas de chiffre dans le mot de passe


def test_login_success(client):
    client.post(
        "/auth/register",
        json={"email": "carol@example.com", "password": "password123"},
    )
    resp = client.post(
        "/auth/login",
        data={"username": "carol@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"email": "dave@example.com", "password": "password123"},
    )
    resp = client.post(
        "/auth/login",
        data={"username": "dave@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_me_requires_authentication(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client, registered_user_headers):
    resp = client.get("/auth/me", headers=registered_user_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


def test_data_export_contains_profile(client, registered_user_headers):
    resp = client.get("/auth/me/data-export", headers=registered_user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["profil"]["email"] == "test@example.com"
    assert data["conversations"] == []


def test_delete_account_then_login_fails(client, registered_user_headers):
    resp = client.delete("/auth/me", headers=registered_user_headers)
    assert resp.status_code == 204

    resp = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 401
