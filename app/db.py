from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

Base = declarative_base()
engine_options = {}
if settings.mysql_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
else:
    engine_options["max_overflow"] = settings.mysql_max_overflow
    engine_options["pool_pre_ping"] = True
    engine_options["pool_recycle"] = settings.mysql_pool_recycle
    engine_options["pool_size"] = settings.mysql_pool_size
    engine_options["pool_timeout"] = settings.mysql_pool_timeout
engine = create_engine(settings.mysql_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
