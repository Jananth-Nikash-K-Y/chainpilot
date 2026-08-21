"""Shared test fixtures — an isolated, seeded SQLite database per session."""
import os
import tempfile

import pytest

# Point the app at a throwaway database *before* app modules import settings.
_TMP_DB = os.path.join(tempfile.mkdtemp(prefix="chainpilot-test-"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.seed import _seed  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seeded_db():
    """Seed once for the whole session; tests that mutate state re-seed."""
    _seed()
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def fresh_client():
    """A client over freshly seeded data, for tests that mutate state."""
    _seed()
    return TestClient(app)
