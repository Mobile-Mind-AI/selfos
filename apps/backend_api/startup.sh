#!/bin/bash

# SelfOS Backend Startup Script
# This script tests imports, sets up database, and starts the application

set -e

echo "🚀 Starting SelfOS Backend..."

echo "🔍 Testing Python imports..."
python scripts/test_imports.py

if [ $? -ne 0 ]; then
    echo "❌ Import test failed. Cannot start application."
    exit 1
fi

echo "✅ All imports successful!"

echo "🗄️ Setting up database..."

# Check if alembic_version table exists and initialize properly
python -c "
import db
from sqlalchemy import inspect
inspector = inspect(db.engine)
if 'alembic_version' not in inspector.get_table_names():
    print('🔄 Initializing Alembic for fresh database...')
    import subprocess
    # For fresh database, don't stamp anything - let upgrade run all migrations
    print('✅ Alembic will run all migrations from scratch')
else:
    print('✅ Alembic already initialized')
"

echo "🔄 Running database migrations..."
alembic upgrade head

echo "🌐 Starting uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info