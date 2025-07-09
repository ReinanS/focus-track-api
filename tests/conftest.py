import pytest
from fastapi.testclient import TestClient

from focus_track_api import app



@pytest.fixture
def client():
    return TestClient(app)