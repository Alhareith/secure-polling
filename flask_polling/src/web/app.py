"""نقطة إنشاء تطبيق Flask."""

from __future__ import annotations

from flask import Flask

from web.settings import load_settings


def create_app(environment: str | None = None) -> Flask:
    """ينشئ تطبيق Flask ويحمّل إعدادات البيئة المطلوبة."""

    app = Flask(__name__)
    app.config.from_mapping(load_settings(environment))
    return app
