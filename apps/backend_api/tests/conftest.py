import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add the backend_api directory to the Python path
backend_api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_api_dir not in sys.path:
    sys.path.insert(0, backend_api_dir)

# Import after path modification
from models import Base
from main import app
from dependencies import get_db, get_current_user

@pytest.fixture(scope="function")
def isolated_test_setup():
    """Create isolated database and override dependencies for each test"""
    # Create unique in-memory database for this test
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        """Test database dependency"""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def override_get_current_user():
        """Test user dependency"""
        return {
            "uid": "test_user_123",
            "email": "testuser@example.com",
            "roles": ["user"]
        }
    
    # Store original overrides
    original_db_override = app.dependency_overrides.get(get_db)
    original_user_override = app.dependency_overrides.get(get_current_user)
    
    # Set test overrides
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    yield {
        "engine": engine,
        "session_local": TestingSessionLocal,
        "db_override": override_get_db,
        "user_override": override_get_current_user
    }
    
    # Restore original overrides
    if original_db_override:
        app.dependency_overrides[get_db] = original_db_override
    else:
        app.dependency_overrides.pop(get_db, None)
        
    if original_user_override:
        app.dependency_overrides[get_current_user] = original_user_override
    else:
        app.dependency_overrides.pop(get_current_user, None)
    
    # Clean up engine
    engine.dispose()

@pytest.fixture
def mock_user():
    """Standard mock user for tests"""
    return {
        "uid": "test_user_123",
        "email": "testuser@example.com",
        "roles": ["user"]
    }

@pytest.fixture(autouse=True)
def cleanup_test_databases():
    """Clean up any test database files after each test"""
    yield
    # Clean up test database files
    test_db_files = [
        "./test.db",
        "./test_tasks.db", 
        "./test_integration.db"
    ]
    for db_file in test_db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except PermissionError:
                pass  # File might be in use, skip cleanup