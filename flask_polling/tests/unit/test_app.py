"""اختبارات إنشاء تطبيق Flask."""

from flask import Flask

from web.app import create_app


def test_create_app_loads_testing_settings(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "testing-secret-only")

    app = create_app("testing")

    assert isinstance(app, Flask)
    assert app.config["APP_ENV"] == "testing"
    assert app.config["TESTING"] is True
    assert app.config["DEBUG"] is False
    assert app.config["SECRET_KEY"] == "testing-secret-only"


def test_create_app_keeps_production_debug_disabled(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "production-secret-only")

    app = create_app("production")

    assert app.config["APP_ENV"] == "production"
    assert app.config["DEBUG"] is False
    assert app.config["SESSION_COOKIE_SECURE"] is True
