#!/bin/bash

# SelfOS Quick Test Script
# This script starts the system and runs comprehensive tests

set -e

echo "🚀 SelfOS Quick Test & Setup"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check for Firebase credentials
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️  Warning: GOOGLE_APPLICATION_CREDENTIALS not set"
    echo "   Firebase authentication may not work"
    echo "   Set the environment variable to your Firebase service account key file"
fi

echo "📦 Building and starting services..."
# Build with no cache to ensure dependencies are fresh
docker-compose build --no-cache backend
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "🏥 Checking service health..."
# Wait for backend to be ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Backend is ready"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Waiting for backend... (attempt $attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Backend failed to start within timeout"
    echo "📋 Checking logs:"
    docker-compose logs backend | tail -20
    echo ""
    echo "🔧 Common fixes:"
    echo "   1. Check DATABASE_URL: docker-compose exec backend env | grep DATABASE"
    echo "   2. Rebuild image: docker-compose build --no-cache backend"
    echo "   3. Check PostgreSQL: docker-compose logs db"
    echo "   4. See docs/TROUBLESHOOTING.md for more help"
    exit 1
fi

echo "🧪 Running comprehensive system tests..."
docker-compose exec backend python scripts/test_system.py

test_result=$?

if [ $test_result -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! All tests passed!"
    echo ""
    echo "Your SelfOS backend is fully operational with:"
    echo "✅ Database connectivity"
    echo "✅ AI event system" 
    echo "✅ All services (progress, storytelling, notifications, memory)"
    echo "✅ Authentication system"
    echo "✅ Complete API workflow"
    echo ""
    echo "🔗 Available endpoints:"
    echo "   📍 API Documentation: http://localhost:8000/docs"
    echo "   🏥 Health Check: http://localhost:8000/health/detailed"
    echo "   🧪 Event Test: http://localhost:8000/health/test-event"
    echo ""
    echo "📖 Next steps:"
    echo "   1. Check API docs at http://localhost:8000/docs"
    echo "   2. Complete a real task to see AI events in action"
    echo "   3. View logs: docker-compose logs -f backend"
else
    echo ""
    echo "❌ SOME TESTS FAILED"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "   1. Check logs: docker-compose logs backend"
    echo "   2. Verify health: curl http://localhost:8000/health/detailed"
    echo "   3. Check database: docker-compose logs db"
    echo "   4. Restart services: docker-compose restart"
fi

echo ""
echo "🛠️  Useful commands:"
echo "   📊 View logs: docker-compose logs -f backend"
echo "   🔄 Restart: docker-compose restart"  
echo "   🛑 Stop: docker-compose down"
echo "   🗑️  Reset: docker-compose down -v && docker-compose up -d"

exit $test_result