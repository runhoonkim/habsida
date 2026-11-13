# tests/test_auth.py
NEW_USER = {
    "email": "ada@example.com",
    "password": "secret123",
    "full_name": "Ada Lovelace"
}

def test_register_creates_user(client):
    """
    Test that registering a new user creates a user in the database.
    """
    resp = client.post("/register", json=NEW_USER)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == NEW_USER["email"]
    assert "hashed_password" not in body    # never leak the hash

def test_register_duplicate_email_is_409(client):
    """
    Test that registering a user with an email that already exists returns a 409 Conflict.
    """
    client.post("/register", json=NEW_USER)  # First registration should succeed
    resp = client.post("/register", json=NEW_USER)  # Second registration should fail
    assert resp.status_code == 409

def test_login_returns_bearer_token(client):
    """
    Test that logging in with valid credentials returns a bearer token.
    """
    client.post("/register", json=NEW_USER)  # Register the user first
    resp = client.post(
        "/token",
        data={
            "username": NEW_USER["email"],
            "password": NEW_USER["password"]
        }
    )
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"

def test_login_with_wrong_password_is_401(client):
    """
    Test that logging in with an incorrect password returns a 401 Unauthorized.
    """
    client.post("/register", json=NEW_USER)  # Register the user first
    resp = client.post(
        "/token",
        data={
            "username": NEW_USER["email"],
            "password": "wrong"
        }
    )
    assert resp.status_code == 401

def test_me_without_token_is_401(client):
    """
    Test that accessing the /me endpoint without a token returns a 401 Unauthorized.
    """
    assert client.get("/me").status_code == 401

def test_me_with_garbage_token_is_401(client):
    """
    Test that accessing the /me endpoint with an invalid token returns a 401 Unauthorized.
    """
    resp = client.get("/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401

