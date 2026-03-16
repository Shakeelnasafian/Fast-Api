from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("AUTH_SECRET", "test-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://testserver")
    monkeypatch.setenv("TRUSTED_HOSTS", "testserver,localhost,127.0.0.1")

    import config
    import db
    import carsharing

    config = importlib.reload(config)
    db = importlib.reload(db)
    carsharing = importlib.reload(carsharing)

    app = carsharing.create_application()

    with TestClient(app) as test_client:
        yield test_client

    db.get_engine().dispose()
    db.get_engine.cache_clear()
    config.get_settings.cache_clear()
