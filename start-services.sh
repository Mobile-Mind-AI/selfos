#!/bin/bash

# SelfOS Services Startup Script
# Convenience script to start SelfOS services

set -e

echo "🚀 SelfOS Services Startup"
echo "========================="

show_usage() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  all          - Start all services (backend + mcp-server + dependencies)"
    echo "  backend      - Start backend API with dependencies"
    echo "  frontend     - Start with frontend (includes backend)"
    echo "  mcp          - Use MCP server startup script (recommended for MCP dev)"
    echo ""
    echo "Examples:"
    echo "  $0 all       # Start backend + MCP server"
    echo "  $0 backend   # Start just backend API"
    echo "  $0 frontend  # Start everything including Flutter web"
    echo "  $0 mcp       # Use MCP-specific startup options"
}

case "${1:-all}" in
    "all")
        echo "📦 Starting Backend + MCP Server..."
        docker-compose up --build backend mcp-server
        ;;

    "backend")
        echo "📦 Starting Backend API..."
        docker-compose up --build backend
        ;;

    "frontend")
        echo "📦 Starting Full Stack (Backend + MCP + Frontend)..."
        docker-compose --profile frontend up --build
        ;;

    "mcp")
        echo "🤖 Using MCP Server startup script..."
        echo "See apps/mcp_server/start_mcp_server.sh for all MCP options"
        ./apps/mcp_server/start_mcp_server.sh
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
