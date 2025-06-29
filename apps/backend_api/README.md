# SelfOS Backend API

This folder contains the FastAPI backend gateway handling all requests for the SelfOS application.

## Overview

The backend API provides comprehensive endpoints for:
- 🔐 **Authentication** - User registration, login, and JWT token management
- 🎯 **Goals** - Create, manage, and track personal goals
- ✅ **Tasks** - Task management with dependencies and progress tracking
- 🏠 **Life Areas** - Organize goals and tasks by life domains
- 📎 **Media Attachments** - File uploads and media management
- ⚙️ **User Preferences** - Personalized settings and configurations
- 📊 **Feedback Logs** - Training data collection for ML/RLHF
- 📖 **Story Sessions** - AI-generated narrative content and social media publishing

## Testing

### Quick Start

Run all tests with the recommended module-by-module approach:

```bash
python run_tests.py
```

### Test Structure

The test suite is organized into:
- **Unit Tests** (`tests/unit/`) - Test individual components in isolation
- **Integration Tests** (`tests/integration/`) - Test component interactions
- **Main API Tests** (`tests/test_main.py`) - Test core API functionality

### Available Test Commands

#### Run All Tests
```bash
# Recommended: Run all tests module-by-module (avoids isolation issues)
python run_tests.py

# Alternative: Run all tests together (may have isolation issues)
python run_tests.py --all-together
```

#### Run Specific Test Categories
```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only  
python run_tests.py --integration

# Main API tests only
python run_tests.py --main
```

#### Run Individual Modules
```bash
# Authentication tests
python run_tests.py --auth

# Goals functionality
python run_tests.py --goals

# Tasks functionality
python run_tests.py --tasks

# Life areas functionality
python run_tests.py --life-areas

# Media attachments
python run_tests.py --media

# User preferences
python run_tests.py --preferences

# Feedback logs
python run_tests.py --feedback

# Story sessions
python run_tests.py --stories
```

#### Advanced Options
```bash
# Run with test coverage report
python run_tests.py --coverage

# Stop on first failure (fast feedback)
python run_tests.py --fast

# Verbose output
python run_tests.py --verbose

# Quiet output
python run_tests.py --quiet
```

### Test Database

Tests use isolated in-memory SQLite databases to ensure:
- ✅ Fast execution
- ✅ No interference between test modules
- ✅ Clean state for each test
- ✅ No impact on development/production databases

### Current Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| Main API | 5 tests | Core endpoints, CORS, health checks |
| Authentication | 7 tests | Registration, login, JWT validation |
| Goals | 9 tests | CRUD operations, validation |
| Tasks | 9 tests | CRUD operations, dependencies |
| Life Areas | 18 tests | CRUD, validation, user isolation |
| Media Attachments | 18 tests | File management, associations |
| User Preferences | 19 tests | Settings, defaults, validation |
| Feedback Logs | 22 tests | ML/RLHF data collection |
| Story Sessions | 26 tests | Narrative generation, publishing |
| Integration | 4 tests | Cross-module workflows |
| **Total** | **137 tests** | **All functionality covered** |

### Test Isolation Strategy

The test suite uses a module-by-module execution strategy to avoid test isolation issues:

1. **Per-Module Databases**: Each test module uses its own in-memory SQLite database
2. **Dependency Overrides**: Clean dependency injection overrides per module
3. **Sequential Execution**: Modules run sequentially to prevent interference
4. **Automatic Cleanup**: Database and dependency cleanup after each module

### Writing New Tests

When adding new functionality:

1. **Create test file**: `tests/unit/test_your_module.py`
2. **Follow naming convention**: `test_*` functions for pytest discovery
3. **Use isolated database**:
   ```python
   # Use in-memory SQLite with StaticPool
   SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
   engine = create_engine(SQLALCHEMY_DATABASE_URL, poolclass=StaticPool)
   ```
4. **Override dependencies**:
   ```python
   app.dependency_overrides[get_db] = override_get_db
   app.dependency_overrides[get_current_user] = override_get_current_user
   ```
5. **Add to test runner**: Update `run_tests.py` module list
6. **Clean up**: Implement proper cleanup in `pytest_sessionfinish`

### Debugging Test Failures

If tests fail:

1. **Run specific module**: `python run_tests.py --module-name`
2. **Check isolation**: Run failing test individually
3. **Review logs**: Use `--verbose` for detailed output
4. **Database state**: Tests use fresh databases, check data setup
5. **Dependency overrides**: Ensure proper mock user/database injection

### Performance

- **Fast execution**: All 137 tests run in ~1 second
- **Parallel potential**: Module-by-module structure allows future parallelization
- **Memory efficient**: In-memory databases with automatic cleanup

### Continuous Integration

The test suite is designed for CI/CD environments:
- No external dependencies
- Deterministic results
- Clear pass/fail reporting
- Detailed error messages
