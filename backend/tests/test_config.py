"""
Tests for configuration
"""
import pytest
import os
import sys

# Добавляем путь к backend для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_test_mode():
    """Verify we're in test mode"""
    assert os.getenv("TESTING") == "1"
