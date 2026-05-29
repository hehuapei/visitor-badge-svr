from sqlalchemy import func, select, text, update

from app.models import Count


class CountRepository:
    def __init__(self, session):
        self.session = session

    def find_by_keyword(self, keyword: str):
        statement = select(Count).where(Count.keyword == keyword).limit(1)
        return self.session.execute(statement).scalars().first()

    def count_keywords(self) -> int:
        statement = select(func.count()).select_from(Count)
        return int(self.session.execute(statement).scalar_one())

    def insert_initial(self, keyword: str, total: int, now: int):
        count = Count(keyword=keyword, total=total, create_time=now, update_time=now)
        self.session.add(count)
        self.session.commit()
        return int(total)

    def increment_existing(self, keyword: str, now: int):
        bind = self.session.get_bind()
        if bind.dialect.name == "mysql":
            result = self.session.execute(
                text(
                    "UPDATE count "
                    "SET total = LAST_INSERT_ID(total + 1), update_time = :now "
                    "WHERE keyword = :keyword"
                ),
                {"keyword": keyword, "now": now},
            )
            if result.rowcount == 0:
                self.session.rollback()
                return None
            total = self.session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one()
            self.session.commit()
            return int(total)

        statement = (
            update(Count)
            .where(Count.keyword == keyword)
            .values(total=Count.total + 1, update_time=now)
        )
        result = self.session.execute(statement)
        if result.rowcount == 0:
            self.session.rollback()
            return None

        total = self.session.execute(
            select(Count.total).where(Count.keyword == keyword).limit(1)
        ).scalar_one()
        self.session.commit()
        return int(total)

    def rollback(self):
        self.session.rollback()
