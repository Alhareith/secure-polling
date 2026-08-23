"""اختبارات اشتراك نماذج SQLite في القاعدة التصريحية نفسها."""

from sqlalchemy.orm import DeclarativeBase

from data.models import Base, PollRecord


def test_poll_record_uses_the_shared_declarative_base() -> None:
    assert issubclass(Base, DeclarativeBase)
    assert PollRecord.metadata is Base.metadata
