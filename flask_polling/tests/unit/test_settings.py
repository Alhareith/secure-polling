"""اختبارات إعدادات البيئات قبل إنشاء تطبيق Flask."""

import pytest

from web.settings import load_settings


def test_testing_settings_keep_debug_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "testing-secret-only")

    settings = load_settings("testing")

    assert settings["APP_ENV"] == "testing"
    assert settings["TESTING"] is True
    assert settings["DEBUG"] is False
    assert settings["SESSION_COOKIE_HTTPONLY"] is True
    assert settings["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_production_settings_require_secure_cookies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "production-secret-only")

    settings = load_settings("production")

    assert settings["DEBUG"] is False
    assert settings["SESSION_COOKIE_SECURE"] is True
    assert settings["PREFERRED_URL_SCHEME"] == "https"


def test_missing_secret_key_is_rejected(monkeypatch: pytest.MonkeyPatch ) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        load_settings("testing")


def test_unknown_environment_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "testing-secret-only")

    with pytest.raises(ValueError, match="Unsupported APP_ENV"):
        load_settings("invalid")
