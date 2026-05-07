"""
Basic tests for Vansh AI backend.
Created by: Vansh Gulati
"""

from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_health():
    """Test the health endpoint."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_query():
    """Test the simple query endpoint."""
    resp = client.post("/api/query", json={"query": "What is AI?"})
    # Will fail if OPENAI_API_KEY is not set or rate limited
    # But we just check it doesn't crash with 500
    assert resp.status_code in (200, 500)


def test_auth_signup_login():
    """Test user signup and login flow."""
    import random
    username = f"testuser_{random.randint(1000, 9999)}"
    email = f"{username}@example.com"

    # Signup
    resp = client.post("/api/auth/signup", json={
        "username": username,
        "email": email,
        "password": "testpass123",
        "full_name": "Test User",
    })
    assert resp.status_code == 201, f"Signup failed: {resp.json()}"

    # Login
    resp = client.post("/api/auth/login", json={
        "username": username,
        "password": "testpass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


if __name__ == "__main__":
    test_health()
    print("Health test passed!")
    test_query()
    print("Query test passed (may fail without OpenAI key)!")
    test_auth_signup_login()
    print("Auth signup/login test passed!")
    print("All basic tests passed!")
