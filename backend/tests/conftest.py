"""
Pytest configuration and fixtures
"""
import pytest
import os
import sys

# Добавляем путь к backend в PYTHONPATH
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Set test environment
os.environ["TESTING"] = "1"


@pytest.fixture(scope="session")
def client():
    """Create a test client for the FastAPI app"""
    from main import app
    from fastapi.testclient import TestClient
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_api_key() -> str:
    """Return a test API key"""
    return "test_key"


@pytest.fixture
def auth_headers(test_api_key: str) -> dict:
    """Return authentication headers"""
    return {"X-API-Key": test_api_key}
