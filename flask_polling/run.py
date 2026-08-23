"""تشغيل محلي لتطبيق Flask في بيئة التطوير."""

from __future__ import annotations

from web.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
