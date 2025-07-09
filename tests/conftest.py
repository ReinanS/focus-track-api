from contextlib import contextmanager
import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event

from focus_track_api import app
from focus_track_api.model import table_registry


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def session():
    engine = create_engine('sqlite:///:memory:')
    table_registry.metadata.create_all(engine)

    with pytest.Session(engine) as session:
        yield session

    table_registry.metadata.drop_all(engine)

@pytest.fixture
def mock_db_time():
    return _mock_db_time

@contextmanager 
def _mock_db_time(*, model, time=datetime(2024, 1, 1)): 

    def fake_time_hook(mapper, connection, target): 
        if hasattr(target, 'created_at'):
            target.created_at = time

    event.listen(model, 'before_insert', fake_time_hook) 

    yield time 

    event.remove(model, 'before_insert', fake_time_hook) 