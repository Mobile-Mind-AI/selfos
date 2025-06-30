import pytest
import os
import sys
import asyncio
from typing import Generator, Dict, Any
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add AI paths first (before backend_api) so AI models take precedence
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
libs_path = os.path.join(project_root, 'libs')
ai_engine_path = os.path.join(project_root, 'apps', 'ai_engine')
for path in [libs_path, ai_engine_path]:
    if path not in sys.path:
        sys.path.insert(0, path)  # Insert first so they take precedence

# Add the backend_api directory to the Python path AFTER AI paths
backend_api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_api_dir not in sys.path:
    sys.path.append(backend_api_dir)  # Append so it comes after AI paths

# Import after path modification (AI models should take precedence for AI functionality)
from models import Base, User
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

# Test environment configuration
@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """Configure environment for testing."""
    # Set test environment variables - preserve AI_PROVIDER from actual environment
    test_env = {
        "TESTING": "true",
        "PYTEST_CURRENT_TEST": "true",
        "AI_ENABLE_CACHING": "false",
        "MEMORY_VECTOR_STORE": "memory",
        "RATE_LIMIT_REQUESTS_PER_MINUTE": "10000",
        "SECRET_KEY": "test-secret-key-do-not-use-in-production"
    }
    
    # Default to local for tests unless explicitly set in environment
    if "AI_PROVIDER" not in os.environ:
        test_env["AI_PROVIDER"] = "local"
    
    # Store original values
    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is not None:
            os.environ[key] = original_value
        elif key in os.environ:
            del os.environ[key]


# Standard test client fixtures
@pytest.fixture(scope="function")
def client():
    """Provide a test client for FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function") 
async def async_client():
    """Provide an async test client for FastAPI application."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Authentication fixtures for standard testing
@pytest.fixture(scope="function")
def test_user(isolated_test_setup):
    """Create a test user in the database."""
    # Mock password hashing for testing (Firebase auth doesn't need local hashes)
    def get_password_hash(password: str) -> str:
        return f"mock_hash_{password}"
    
    setup = isolated_test_setup
    session = setup["session_local"]()
    
    try:
        user = User(
            uid="test_user_123",
            email="test@example.com"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        yield user
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_user_token(client, test_user) -> str:
    """Get authentication token for test user."""
    response = client.post(
        "/auth/login",
        json={"username": test_user.email, "password": "testpassword123"}
    )
    assert response.status_code == 200
    token_data = response.json()
    return token_data["access_token"]


@pytest.fixture(scope="function")
def get_test_user_headers(test_user_token) -> Dict[str, str]:
    """Get authentication headers for test requests."""
    return {"Authorization": f"Bearer {test_user_token}"}


# Live server testing fixtures
@pytest.fixture(scope="session")
def live_server_url():
    """Get URL for live server testing."""
    return os.getenv("TEST_SERVER_URL", "http://localhost:8000")


@pytest.fixture(scope="function")
async def live_client(live_server_url):
    """Provide async client for testing against live server."""
    if os.getenv("TEST_SERVER_URL"):
        # Use live server
        async with httpx.AsyncClient(base_url=live_server_url, timeout=30.0) as ac:
            yield ac
    else:
        # Use test client as fallback
        async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
            yield ac


@pytest.fixture(scope="function")
def live_server_auth_headers(live_server_url):
    """Get authentication headers for live server testing."""
    if not os.getenv("TEST_SERVER_URL"):
        # Use regular test fixture for non-live testing
        pytest.skip("Live server testing not enabled")
    
    import requests
    
    # Register test user on live server
    register_response = requests.post(
        f"{live_server_url}/auth/register",
        json={
            "email": "livetest@example.com",
            "password": "livetestpassword123", 
            "full_name": "Live Test User"
        }
    )
    
    # Login to get token (user might already exist)
    login_response = requests.post(
        f"{live_server_url}/auth/login",
        data={"username": "livetest@example.com", "password": "livetestpassword123"}
    )
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        pytest.skip("Could not authenticate with live server")


@pytest.fixture(scope="session")
def ensure_live_server_running(live_server_url):
    """Ensure live server is running for live tests."""
    if not os.getenv("TEST_SERVER_URL"):
        yield  # Skip for non-live testing
        return
    
    import requests
    import time
    
    # Wait for server to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{live_server_url}/health", timeout=5)
            if response.status_code == 200:
                yield
                return
        except requests.exceptions.RequestException:
            pass
        
        if i < max_retries - 1:
            time.sleep(1)
    
    pytest.skip(f"Live server not available at {live_server_url}")


# Sample data fixtures
@pytest.fixture(scope="function")
def sample_goal_data():
    """Provide sample goal data for testing."""
    return {
        "title": "Learn Python Programming",
        "description": "Master Python programming fundamentals",
        "life_area_id": 1,
        "target_date": "2024-12-31",
        "status": "active"
    }


@pytest.fixture(scope="function")
def sample_task_data():
    """Provide sample task data for testing."""
    return {
        "title": "Complete Python Tutorial",
        "description": "Work through basic Python tutorial",
        "goal_id": 1,
        "priority": "medium",
        "status": "pending"
    }


@pytest.fixture(scope="function")
def sample_chat_data():
    """Provide sample chat data for testing."""
    return {
        "message": "Help me plan my learning goals",
        "conversation_history": [],
        "user_context": {"new_user": True}
    }


@pytest.fixture(scope="function")
def sample_goal_decomposition_data():
    """Provide sample goal decomposition data for testing."""
    return {
        "goal_description": "Learn to play guitar",
        "life_areas": [{"id": 1, "name": "Hobbies", "description": "Personal interests"}],
        "existing_goals": [],
        "user_preferences": {"learning_style": "hands-on"},
        "additional_context": "Complete beginner"
    }


# Performance testing fixture
@pytest.fixture(scope="function")
def performance_timer():
    """Provide a simple performance timer for tests."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


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
        "./test_integration.db",
        "./test_selfos.db",
        "./test_selfos.db-shm",
        "./test_selfos.db-wal"
    ]
    for db_file in test_db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except PermissionError:
                pass  # File might be in use, skip cleanup


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "ai: AI-related tests") 
    config.addinivalue_line("markers", "memory: Memory service tests")
    config.addinivalue_line("markers", "chat: Chat simulation tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "live: Tests against live server")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add markers based on test file names
        if "ai" in str(item.fspath):
            item.add_marker(pytest.mark.ai)
        if "memory" in str(item.fspath):
            item.add_marker(pytest.mark.memory)
        if "chat" in str(item.fspath):
            item.add_marker(pytest.mark.chat)
        
        # Add slow marker to specific tests
        if "stress" in item.name or "performance" in item.name or "concurrent" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Add live marker to tests using live server fixtures
        if hasattr(item.function, 'pytestmark'):
            for mark in item.function.pytestmark:
                if 'live_server' in str(mark) or 'live_client' in str(mark):
                    item.add_marker(pytest.mark.live)