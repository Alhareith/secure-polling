"""اختبارات إنشاء تطبيق Flask."""

import pytest
from flask import Flask

from web.app import create_app


def test_create_app_loads_testing_settings(app: Flask) -> None:
    assert isinstance(app, Flask)
    assert app.config["APP_ENV"] == "testing"
    assert app.config["TESTING"] is True
    assert app.config["DEBUG"] is False
    assert app.config["SECRET_KEY"] == "testing-secret-only"
    assert app.extensions["polling_db_engine"].url.database == ":memory:"
    assert callable(app.extensions["polling_session_factory"])


def test_create_app_keeps_production_debug_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "production-secret-only")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///production.db")

    app = create_app("production")

    assert app.config["APP_ENV"] == "production"
    assert app.config["DEBUG"] is False
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.extensions["polling_db_engine"].url.database == "production.db"
