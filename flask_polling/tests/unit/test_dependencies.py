"""اختبارات توفر الاعتمادات التشغيلية المطلوبة."""

import sqlalchemy


def test_sqlalchemy_major_version_is_supported() -> None:
    """يضمن اعتماد المشروع على SQLAlchemy 2.x قبل بناء طبقة التخزين."""

    assert sqlalchemy.__version__.split(".", maxsplit=1)[0] == "2"
