import os
import shutil
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as app_db
from app.database import Base, get_db
from app.config import settings
from app.main import app

# Create a temporary directory for test storage & test database
@pytest.fixture(scope="session", autouse=True)
def setup_test_storage():
    test_dir = Path(tempfile.mkdtemp(prefix="cert_test_storage_"))
    original_storage = settings.STORAGE_DIR
    settings.STORAGE_DIR = test_dir
    yield test_dir
    settings.STORAGE_DIR = original_storage
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)

TEST_DB_FILE = "./test_certificates.db"
TEST_SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    test_engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Override global database engine and SessionLocal in app.database & services
    app_db.engine = test_engine
    app_db.SessionLocal = TestSessionLocal
    
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except PermissionError:
            pass

@pytest.fixture(scope="function")
def db_session():
    session = app_db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c
