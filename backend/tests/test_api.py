from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """API is running and reachable."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_register_user():
    """Register endpoint exists and handles requests."""
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    })
    assert response.status_code in [201, 400]  # 400 if user already exists

def test_docs_available():
    """FastAPI auto-generated docs are accessible.
    TODO: Replace with test_create_relationship and test_computed_overall
    once CRUD endpoints are built in Phase 1.
    """
    response = client.get("/docs")
    assert response.status_code == 200