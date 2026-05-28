import time

from sqlalchemy.exc import IntegrityError

from app.repository import CountRepository


class CountService:
    def __init__(self, session):
        self.repository = CountRepository(session)

    def count(self, keyword: str, action: str) -> int:
        if keyword == "":
            return 0
        if action == "update":
            return self._update_count(keyword)
        return self._query_count(keyword)

    def _query_count(self, keyword: str) -> int:
        count = self.repository.find_by_keyword(keyword)
        if count is not None:
            return int(count.total)

        now = int(time.time() * 1000)
        try:
            return self.repository.insert_initial(keyword, 0, now)
        except IntegrityError:
            self.repository.rollback()
            count = self.repository.find_by_keyword(keyword)
            if count is None:
                raise
            return int(count.total)

    def _update_count(self, keyword: str) -> int:
        total = self.repository.increment_existing(keyword, int(time.time() * 1000))
        if total is not None:
            return total

        now = int(time.time() * 1000)
        try:
            return self.repository.insert_initial(keyword, 1, now)
        except IntegrityError:
            self.repository.rollback()

        total = self.repository.increment_existing(keyword, int(time.time() * 1000))
        if total is not None:
            return total
        raise RuntimeError("failed to update count after concurrent insert")
