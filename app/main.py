from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.config import settings
from app.db import engine, get_session
from app.service import CountService


def validate_schema():
    inspector = inspect(engine)
    if "count" not in inspector.get_table_names():
        raise RuntimeError("count table is missing; initialize the database with schema.sql before startup")

    columns = {column["name"]: column for column in inspector.get_columns("count")}
    keyword = columns.get("keyword")
    if keyword is None:
        raise RuntimeError("count table is missing keyword column")
    if keyword.get("nullable", True):
        raise RuntimeError("count.keyword must be NOT NULL; rebuild or migrate the database schema")

    unique_indexes = inspector.get_unique_constraints("count")
    has_keyword_unique = any(
        constraint.get("column_names") == ["keyword"] for constraint in unique_indexes
    )
    if not has_keyword_unique:
        raise RuntimeError("count.keyword must be UNIQUE; rebuild or migrate the database schema")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_schema()
    yield


def get_count_service(session: Session = Depends(get_session)):
    return CountService(session)


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    @app.get("/count")
    def count(
        keyword: str = "",
        action: str = "",
        service: CountService = Depends(get_count_service),
    ):
        return {"value": service.count(keyword, action)}

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.server_port,
        workers=settings.server_workers,
    )
