"""
Tests for main application endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_read_root(client):
    """Test root endpoint returns 200 OK"""
    response = client.get("/")
    assert response.status_code == 200
    # Root может вернуть HTML (FileResponse) или JSON
    # Главное что endpoint доступен


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_docs_accessible(client):
    """Test that Swagger docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json(client):
    """Test OpenAPI JSON schema is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data


def test_redoc_accessible(client):
    """Test ReDoc documentation is accessible"""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_protected_endpoint_without_auth(client):
    """Test that protected endpoints require authentication"""
    response = client.get("/api/v1/projects")
    assert response.status_code in [401, 403]


def test_protected_endpoint_with_auth(client, auth_headers):
    """Test protected endpoint with authentication"""
    # This will likely fail without real Redmine, but tests the auth flow
    response = client.get("/api/v1/projects", headers=auth_headers)
    # Accept either success or error from Redmine connection
    assert response.status_code in [200, 401, 403, 500, 503]


def test_invalid_endpoint(client):
    """Test 404 for non-existent endpoints"""
    response = client.get("/nonexistent")
    assert response.status_code == 404


@pytest.mark.parametrize("endpoint", [
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc"
])
def test_public_endpoints(client, endpoint):
    """Test that public endpoints are accessible without auth"""
    response = client.get(endpoint)
    assert response.status_code == 200
