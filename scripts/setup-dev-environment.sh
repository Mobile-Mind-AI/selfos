#!/bin/bash
# Setup script for SelfOS development environment
set -e

echo "🚀 Setting up SelfOS development environment..."

# Check Python version
if ! python3 --version | grep -E "3\.(10|11|12)" > /dev/null; then
    echo "❌ Python 3.10+ is required. Current version:"
    python3 --version
    exit 1
fi

echo "✅ Python version check passed"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔗 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install development tools
echo "🔧 Installing development tools..."
pip install \
    pre-commit \
    black \
    isort \
    ruff \
    mypy \
    pytest \
    pytest-cov \
    pytest-xdist \
    pytest-asyncio \
    coverage[toml] \
    safety \
    bandit \
    pip-audit

# Install backend API dependencies
echo "📚 Installing backend API dependencies..."
cd apps/backend_api
pip install -r requirements.txt
cd ../..

# Setup pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install --install-hooks

# Create test database and environment files
echo "🗄️ Setting up test environment..."
cd apps/backend_api

# Create .env.example if it doesn't exist
if [ ! -f .env.example ]; then
    cat > .env.example << 'EOF'
DATABASE_URL=postgresql://selfos:selfos@localhost:5432/selfos_dev
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
AI_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
MEMORY_VECTOR_STORE=weaviate
WEAVIATE_URL=http://localhost:8080
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-key.json
EOF
fi

# Create test environment
cat > .env.test << 'EOF'
DATABASE_URL=sqlite:///./test_selfos.db
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=test-secret-key-do-not-use-in-production
AI_PROVIDER=local
MEMORY_VECTOR_STORE=memory
GOOGLE_APPLICATION_CREDENTIALS=/tmp/dummy-firebase.json
TESTING=true
PYTEST_CURRENT_TEST=true
EOF

# Create dummy Firebase credentials for testing
echo '{"type": "service_account", "project_id": "test-project"}' > /tmp/dummy-firebase.json

cd ../..

echo "✅ Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Activate the virtual environment: source .venv/bin/activate"
echo "  2. Copy apps/backend_api/.env.example to .env and configure"
echo "  3. Set up PostgreSQL and Redis (or use Docker: docker-compose up postgres redis)"
echo "  4. Run database migrations: cd apps/backend_api && alembic upgrade head"
echo "  5. Run tests: ./scripts/run-tests.sh"
echo ""
echo "🔧 Available commands:"
echo "  ./scripts/run-tests.sh           - Run all tests"
echo "  ./scripts/run-tests.sh --backend - Run backend tests only"
echo "  ./scripts/run-tests.sh --mcp     - Run MCP server tests only"
echo "  ./scripts/lint.sh                - Run linting and formatting"
echo "  pre-commit run --all-files       - Run all pre-commit hooks"
