#!/bin/bash

# Start SelfOS MCP Server
# Multiple ways to run the MCP server for different use cases

set -e

echo "🚀 SelfOS MCP Server Startup Options"
echo "======================================="

# Function to show usage
show_usage() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  docker       - Start MCP server in Docker (recommended)"
    echo "  standalone   - Start MCP server standalone"
    echo "  fastapi      - Start MCP server with FastAPI integration"
    echo "  stdio        - Start MCP server with stdio transport (for AI agents)"
    echo "  test         - Run MCP server tests"
    echo ""
    echo "Examples:"
    echo "  $0 docker      # Start with Docker Compose"
    echo "  $0 standalone  # Run locally for development"
    echo "  $0 test        # Run the test suite"
}

# Parse command line arguments
case "${1:-docker}" in
    "docker")
        echo "📦 Starting Backend + MCP Server with Docker Compose..."
        echo "This will start both backend API and MCP server with dependencies."
        echo ""
        echo "Access points:"
        echo "  - Backend API: http://localhost:8000"
        echo "  - MCP Server:  http://localhost:8001"
        echo "  - Health:      http://localhost:8001/health"
        echo ""
        cd ../..
        docker-compose up --build backend mcp-server
        ;;
        
    "standalone")
        echo "🔧 Starting MCP Server in standalone mode..."
        echo "Make sure you have the backend_api dependencies installed:"
        echo "  cd apps/backend_api && pip install -r requirements.txt"
        echo ""
        python fastapi_integration.py --host 0.0.0.0 --port 8001 --reload
        ;;
        
    "fastapi")
        echo "🌐 Starting MCP Server with FastAPI integration..."
        python fastapi_integration.py --host 127.0.0.1 --port 8001 --reload
        ;;
        
    "stdio")
        echo "📱 Starting MCP Server with stdio transport..."
        echo "This mode is for AI agents that communicate via standard input/output."
        python cli.py --transport stdio
        ;;
        
    "test")
        echo "🧪 Running MCP Server tests..."
        python run_tests.py --coverage
        ;;
        
    "help"|"-h"|"--help")
        show_usage
        ;;
        
    *)
        echo "❌ Unknown option: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac