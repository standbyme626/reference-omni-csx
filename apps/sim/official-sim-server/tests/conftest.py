import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[4]
SERVICE_ROOT = Path(__file__).resolve().parents[1]


def _prepend_path(path: Path) -> None:
    path_str = str(path)
    if path_str in sys.path:
        sys.path.remove(path_str)
    sys.path.insert(0, path_str)


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name, None)


_purge_app_modules()
_prepend_path(REPO_ROOT)
_prepend_path(SERVICE_ROOT)


def _activate_official_sim_imports() -> None:
    _purge_app_modules()
    _prepend_path(REPO_ROOT)
    _prepend_path(SERVICE_ROOT)


def pytest_collect_file(file_path, parent):
    _activate_official_sim_imports()
    return None


def pytest_runtest_setup(item):
    _activate_official_sim_imports()


TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/official_sim"


@pytest.fixture(scope="function")
def test_db():
    test_engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    from app.core.database import Base

    importlib.import_module("app.models.models")

    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()
    try:
        yield session, test_engine
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_db):
    session, test_engine = test_db

    from app.core.database import get_db
    from app.main import app

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
