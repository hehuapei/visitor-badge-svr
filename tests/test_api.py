from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.main import create_app, get_count_service


class StubService:
    def count(self, keyword, action):
        if keyword == "":
            return 0
        if action == "update":
            return 2
        return 1


@contextmanager
def build_client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_count_service] = lambda: StubService()
    with TestClient(app) as client:
        yield client


def test_count_endpoint_returns_value_field():
    with build_client() as client:
        response = client.get("/count", params={"keyword": "demo", "action": "query"})

    assert response.status_code == 200
    assert response.json() == {"value": 1}


def test_count_endpoint_defaults_to_zero():
    with build_client() as client:
        response = client.get("/count")

    assert response.status_code == 200
    assert response.json() == {"value": 0}
