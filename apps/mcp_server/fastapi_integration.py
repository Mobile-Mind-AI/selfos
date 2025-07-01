#!/usr/bin/env python3
"""
FastAPI Integration for SelfOS MCP Server

Runs the MCP server integrated with FastAPI for WebSocket and SSE endpoints.
This allows the MCP server to be accessible via HTTP/WebSocket from web clients.
"""

import asyncio
import logging
import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add backend_api to path for imports
sys.path.append(str(Path(__file__).parent.parent / "backend_api"))

from server import SelfOSMcpServer
from config import MCPConfig

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create FastAPI application with MCP server integration."""
    
    # Create FastAPI app
    app = FastAPI(
        title="SelfOS MCP Server",
        description="Model Context Protocol server for SelfOS AI integration",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create MCP server
    config = MCPConfig.from_env()
    mcp_server = SelfOSMcpServer(config)
    
    # Mount MCP transport endpoints
    sse_app = mcp_server.transports["sse"].get_app()
    websocket_app = mcp_server.transports["websocket"].get_app()
    
    # Mount the sub-applications
    app.mount("/mcp/sse", sse_app)
    app.mount("/mcp/ws", websocket_app)
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "SelfOS MCP Server",
            "version": "1.0.0",
            "endpoints": {
                "sse": "/mcp/sse",
                "websocket": "/mcp/ws",
                "health": "/health"
            }
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "server": "selfos-mcp-server",
            "version": "1.0.0",
            "capabilities": mcp_server.get_capabilities()
        }
    
    @app.get("/mcp/capabilities")
    async def capabilities():
        """Get MCP server capabilities."""
        return mcp_server.get_capabilities()
    
    # Store server instance for startup/shutdown
    app.state.mcp_server = mcp_server
    
    return app


async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting SelfOS MCP Server with FastAPI integration")
    mcp_server = app.state.mcp_server
    
    # Initialize transport layers
    await mcp_server.transports["sse"].start()
    await mcp_server.transports["websocket"].start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down SelfOS MCP Server")
    await mcp_server.stop()


def main():
    """Main entry point for FastAPI integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SelfOS MCP Server with FastAPI")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to bind to (default: 8001)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create app
    app = create_app()
    
    # Configure lifespan
    app.router.lifespan_context = lifespan
    
    logger.info(f"Starting MCP Server on {args.host}:{args.port}")
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level.lower(),
        reload=args.reload
    )


if __name__ == "__main__":
    main()