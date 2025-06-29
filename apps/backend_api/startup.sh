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
python -c "
import db
import models
print('Creating database tables...')
db.Base.metadata.create_all(bind=db.engine)
print('Database tables created successfully!')
"

echo "🔄 Running database migrations..."
alembic upgrade head || echo "⚠️  Alembic migration failed, continuing with table creation"

echo "🌐 Starting uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info