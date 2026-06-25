"""
conftest.py
Shared pytest fixtures and path setup.

Ensures the project root is importable (so `import app` works regardless of how
pytest is invoked) and isolates the in-memory auth token store between tests.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture(autouse=True)
def _clear_token_store():
    """Reset auth.TOKEN_STORE before each test so tokens don't leak across cases."""
    from app import auth

    auth.TOKEN_STORE.clear()
    yield
    auth.TOKEN_STORE.clear()
