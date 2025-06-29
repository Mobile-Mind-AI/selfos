#!/bin/bash

# SelfOS Fix and Start Script
# This script fixes common Docker issues and starts the system

set -e

echo "🔧 SelfOS Fix and Start"
echo "======================"

echo "🛑 Stopping any running services..."
docker-compose down -v

echo "🧹 Cleaning up Docker..."
# Remove old images
docker rmi $(docker images "selfos*" -q) 2>/dev/null || true

echo "🔨 Building fresh backend image..."
docker-compose build --no-cache backend

echo "🧪 Testing imports locally first..."
cd apps/backend_api
python test_imports.py
cd ../..

echo "📦 Starting services..."
docker-compose up -d

echo "⏳ Waiting for database to be ready..."
until docker-compose exec -T db pg_isready -U selfos; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done

echo "⏳ Waiting for backend to be ready..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Waiting for backend... (attempt $attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Backend failed to start. Checking logs..."
    echo "Backend logs:"
    docker-compose logs backend | tail -30
    echo ""
    echo "Database logs:"
    docker-compose logs db | tail -10
    exit 1
fi

echo "🏥 Running health check..."
curl -s http://localhost:8000/health/detailed | jq '.' || {
    echo "Health check failed, but service is running. Raw response:"
    curl -s http://localhost:8000/health
}

echo ""
echo "🎉 SUCCESS! System is running!"
echo ""
echo "🔗 Available endpoints:"
echo "   📍 API: http://localhost:8000"
echo "   📚 Docs: http://localhost:8000/docs"
echo "   🏥 Health: http://localhost:8000/health/detailed"
echo "   🧪 Test Event: curl -X POST http://localhost:8000/health/test-event"
echo ""
echo "🧪 To run full system tests:"
echo "   ./scripts/quick-test.sh"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f backend"