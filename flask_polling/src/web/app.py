"""نقطة إنشاء تطبيق Flask."""

from __future__ import annotations

from flask import Flask

from data.db import create_session_factory, create_sqlite_engine
from web.settings import load_settings


def create_app(environment: str | None = None) -> Flask:
    """ينشئ تطبيق Flask ويحمّل إعدادات البيئة المطلوبة."""

    app = Flask(__name__)
    app.config.from_mapping(load_settings(environment))
    engine = create_sqlite_engine(app.config["DATABASE_URL"])
    app.extensions["polling_db_engine"] = engine
    app.extensions["polling_session_factory"] = create_session_factory(engine)
    return app
