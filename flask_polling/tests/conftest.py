"""Fixtures مشتركة لاختبارات Flask."""

from __future__ import annotations

import pytest
from flask import Flask

from web.app import create_app


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch) -> Flask:
    """ينشئ تطبيق Flask في بيئة الاختبار مع سر مؤقت."""

    monkeypatch.setenv("SECRET_KEY", "testing-secret-only")
    return create_app("testing")
