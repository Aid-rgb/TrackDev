"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

# Set test environment
os.environ["TESTING"] = "1"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    from main import app
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_api_key():
    """Return a test API key"""
    return "test_key"


@pytest.fixture
def auth_headers(test_api_key):
    """Return authentication headers"""
    return {"X-API-Key": test_api_key}
