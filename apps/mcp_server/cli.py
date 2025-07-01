#!/usr/bin/env python3
"""
SelfOS MCP Server CLI

Command-line interface for running and testing the SelfOS MCP server.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add backend_api to path for imports
sys.path.append(str(Path(__file__).parent.parent / "backend_api"))

from server import SelfOSMcpServer
from config import MCPConfig


def setup_logging(level: str = "INFO"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler('mcp_server.log')
        ]
    )


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="SelfOS MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse", "websocket"], 
        default="stdio",
        help="Transport layer to use"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
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
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        if args.config:
            # TODO: Load from file
            config = MCPConfig.from_env()
        else:
            config = MCPConfig.from_env()
        
        # Validate configuration
        errors = config.validate()
        if errors:
            logger.error(f"Configuration errors: {errors}")
            sys.exit(1)
        
        # Create and start server
        server = SelfOSMcpServer(config)
        logger.info(f"Starting SelfOS MCP Server with {args.transport} transport")
        
        await server.start(args.transport)
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())