# SelfOS Developer Guide

This guide covers everything you need to know to develop, deploy, and maintain SelfOS.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Environment](#development-environment)
3. [Command Reference](#command-reference)
4. [Development Workflows](#development-workflows)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- Python 3.11+

### 30-Second Setup

```bash
# Clone and start the stack
git clone <repository-url>
cd selfos
docker-compose up --build

# Verify services
curl http://localhost:8000/health
```

Expected response: `{"status": "healthy"}`

## Development Environment

### Docker Development (Recommended)

The simplest way to get started is with Docker Compose.

```bash
# Build and start all services
docker-compose up --build

# Start in the background
docker-compose up -d

# Stop all services
docker-compose down
```

### Local Development

If you prefer to run the backend locally without Docker:

```bash
# Navigate to the backend directory
cd apps/backend_api

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Configuration

You'll need a Firebase service account to handle authentication.

1.  Create a Firebase project.
2.  Generate a private key file (service account JSON).
3.  Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of this file.

## Command Reference

### Docker Commands

-   `docker-compose up --build`: Build and start all services.
-   `docker-compose down`: Stop all services.
-   `docker-compose logs -f backend_api`: Follow the logs for the backend service.
-   `docker-compose exec backend_api alembic upgrade head`: Run database migrations inside the container.

### Testing Commands

From the `apps/backend_api` directory:

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run with coverage report
python run_tests.py --coverage
```

## Development Workflows

### Feature Development

1.  **Create a new branch**: `git checkout -b feature/your-feature-name`
2.  **Make your changes**: Implement your feature, including any necessary model changes.
3.  **Create a database migration**: If you changed the models, run `alembic revision --autogenerate -m "Your message"`
4.  **Write tests**: Add unit and/or integration tests for your new feature.
5.  **Run the test suite**: `python run_tests.py`
6.  **Commit and push**: `git commit -m "Your message" && git push`

### Code Quality

Please ensure your code is formatted with `black` and passes `flake8` and `mypy` checks before submitting a pull request.

## Testing

The backend has a comprehensive test suite using `pytest`. However, many tests are currently failing.

### Test Status
-   **Unit Tests**: Cover individual components and business logic.
-   **Integration Tests**: Test the API endpoints and their interaction with the database.
-   **Current State**: A significant number of tests are failing and need to be fixed.

## Troubleshooting

### Common Issues

-   **Database Connection Errors**: Ensure the PostgreSQL container is running and that the `DATABASE_URL` is correctly configured.
-   **Authentication Errors**: Make sure the `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set correctly.
-   **Port Conflicts**: If you get an error that a port is already in use, stop any other services running on that port.

---

For more detailed information, please refer to the other documentation files in this directory.
