"""إعدادات Flask المنفصلة حسب البيئة.

يبقى هذا الملف مسؤولًا عن الإعدادات فقط؛ لا ينشئ التطبيق ولا يقرأ قاعدة بيانات.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any


class BaseSettings:
    """إعدادات مشتركة لا تتضمن أي سر."""

    APP_ENV = "base"
    DEBUG = False
    TESTING = False
    MAX_CONTENT_LENGTH = 32 * 1024
    SESSION_COOKIE_NAME = "secure_polling_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False


class DevelopmentSettings(BaseSettings):
    """إعدادات التطوير المحلي."""

    APP_ENV = "development"
    DEBUG = True


class TestingSettings(BaseSettings):
    """إعدادات الاختبارات التلقائية."""

    APP_ENV = "testing"
    TESTING = True
    PROPAGATE_EXCEPTIONS = True


class ProductionSettings(BaseSettings):
    """إعدادات التشغيل النهائي الآمن."""

    APP_ENV = "production"
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"


SETTINGS_BY_ENV = {
    "development": DevelopmentSettings,
    "testing": TestingSettings,
    "production": ProductionSettings,
}


def _class_settings(settings_class: type[BaseSettings]) -> dict[str, Any]:
    """يجمع إعدادات الطبقة الأساسية والبيئة المطلوبة مع أولوية للأخيرة."""

    values: dict[str, Any] = {}
    for parent in reversed(settings_class.mro()):
        values.update(
            {
                key: value
                for key, value in vars(parent).items()
                if key.isupper() and not key.startswith("_")
            }
        )
    return values


def load_settings(environment: str | None = None) -> Mapping[str, Any]:
    """يعيد إعدادات البيئة المطلوبة بعد التحقق من وجود السر في البيئة."""

    selected_environment = environment or os.environ.get("APP_ENV", "development")
    try:
        settings_class = SETTINGS_BY_ENV[selected_environment]
    except KeyError as error:
        allowed = ", ".join(sorted(SETTINGS_BY_ENV))
        message = f"Unsupported APP_ENV: {selected_environment}. Allowed: {allowed}"
        raise ValueError(message) from error

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY must be provided through the environment.")

    values = _class_settings(settings_class)
    values["SECRET_KEY"] = secret_key
    return values
