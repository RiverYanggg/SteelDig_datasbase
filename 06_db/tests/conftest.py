"""共享 fixture：数据库连接。"""
from __future__ import annotations

import pytest
from steeldig_db.config import settings
from steeldig_db.db import connect


@pytest.fixture(scope="session")
def conn():
    with connect() as c:
        yield c


@pytest.fixture(scope="session")
def dsn() -> str:
    return settings.dsn
