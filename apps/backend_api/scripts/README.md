# Backend API Scripts

This directory contains operational scripts for the SelfOS backend API.

## Scripts

### `test_imports.py`
- **Purpose**: Validates all Python imports before application startup
- **Used by**: `startup.sh` (Docker container startup process)
- **Usage**: `python scripts/test_imports.py`
- **Description**: Tests that all critical modules can be imported correctly, helping catch import errors early in the deployment process

### `test_system.py`
- **Purpose**: Comprehensive end-to-end system integration tests
- **Used by**: `../../../scripts/quick-test.sh` (system testing script)
- **Usage**: `python scripts/test_system.py`
- **Description**: Tests the complete system including:
  - Health checks (basic and detailed)
  - Database migration status
  - Event system functionality
  - All AI services (progress, storytelling, notifications, memory)
  - Authentication system
  - Complete API workflow (create user → life area → goal → task → complete task → AI events)

## Notes

- Both scripts automatically add the parent directory to Python path to import app modules
- These are operational tools, not unit tests (unit tests are in the `tests/` directory)
- Scripts are designed to be run from the backend_api root directory
- Used in production deployment and CI/CD processes