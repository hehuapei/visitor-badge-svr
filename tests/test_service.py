import tempfile
import threading
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Count
from app.service import CountService


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return session_factory()


def test_count_returns_zero_for_empty_keyword():
    session = build_session()
    service = CountService(session)

    assert service.count("", "") == 0


def test_count_initializes_missing_keyword_to_zero_for_query():
    session = build_session()
    service = CountService(session)

    result = service.count("demo", "query")

    stored = session.query(Count).filter_by(keyword="demo").one()
    assert result == 0
    assert stored.total == 0
    assert stored.create_time is not None
    assert stored.update_time is not None


def test_count_updates_when_action_is_update():
    session = build_session()
    service = CountService(session)

    first = service.count("demo", "query")
    second = service.count("demo", "update")

    assert first == 0
    assert second == 1


def test_count_initial_update_starts_missing_keyword_at_one():
    session = build_session()
    service = CountService(session)

    result = service.count("demo", "update")

    stored = session.query(Count).filter_by(keyword="demo").one()
    assert result == 1
    assert stored.total == 1


def test_count_treats_keywords_as_distinct_values():
    session = build_session()
    service = CountService(session)

    first = service.count("ABC", "query")
    second = service.count("abc", "query")

    assert first == 0
    assert second == 0


def test_count_accumulates_under_concurrent_updates():
    with tempfile.TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "thread-demo.sqlite3"
        engine = create_engine(
            f"sqlite:///{database_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

        def worker():
            session = session_factory()
            try:
                service = CountService(session)
                service.count("thread-demo", "update")
            finally:
                session.close()

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        session = session_factory()
        try:
            stored = session.query(Count).filter_by(keyword="thread-demo").one()
            assert stored.total == 10
        finally:
            session.close()
