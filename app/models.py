from sqlalchemy import BigInteger, Column, String
from sqlalchemy.ext.compiler import compiles

from app.db import Base


@compiles(BigInteger, "sqlite")
def compile_big_integer_sqlite(_type, compiler, **kw):
    return "INTEGER"


class Count(Base):
    __tablename__ = "count"
    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_bin"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    keyword = Column(String(255), nullable=False, unique=True)
    total = Column(BigInteger, nullable=False)
    create_time = Column(BigInteger, nullable=True)
    update_time = Column(BigInteger, nullable=True)
