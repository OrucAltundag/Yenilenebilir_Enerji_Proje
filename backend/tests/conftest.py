"""Test ortak kurulumu.

Modül seviyesinde TestClient lifespan'i otomatik tetiklemediği için DB
tablolarını burada oluştururuz.
"""

import pytest

from app.db.session import init_db


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    init_db()
    yield
