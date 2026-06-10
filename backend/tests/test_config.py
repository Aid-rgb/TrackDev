"""
Tests for configuration
"""
import pytest
import os
import sys

# Добавляем путь к backend для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_environment_variables():
    """Test that required environment variables are set"""
    # These should be set by the test environment
    assert os.getenv("DATABASE_URL") is not None
    assert os.getenv("REDMINE_URL") is not None


def test_test_mode():
    """Verify we're in test mode"""
    assert os.getenv("TESTING") == "1"
