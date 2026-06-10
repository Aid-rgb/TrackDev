"""
Tests for configuration
"""
import pytest
import os


def test_environment_variables():
    """Test that required environment variables are set"""
    # These should be set by the test environment
    assert os.getenv("DATABASE_URL") is not None
    assert os.getenv("REDMINE_URL") is not None


def test_config_loading():
    """Test configuration loading"""
    from app.core.config import settings
    
    assert settings is not None
    assert hasattr(settings, "redmine_url")
    assert hasattr(settings, "database_url")


def test_test_mode():
    """Verify we're in test mode"""
    assert os.getenv("TESTING") == "1"
