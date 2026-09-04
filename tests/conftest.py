import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client() -> TestClient:
    """ Fixture que fornece um cliente HTTP para testes de integração com a API. """
    return TestClient(app)

def pytest_collection_modifyitems(items):
    """ Garante a ordenação : Unitários antes de Integração """
    order_priority = { "unit": 1, "blackbox": 2, "whitebox": 3, "integration": 4 }

    def get_priority(item):
        for mark in item.iter_markers():
            if mark.name in order_priority:
                return order_priority[mark.name]
            return 99

    items.sort(key=get_priority)