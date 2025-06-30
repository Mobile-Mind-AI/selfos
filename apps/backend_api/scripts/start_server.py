#!/usr/bin/env python3
"""
SelfOS Development Server Starter

Simple script to start the SelfOS backend API server with proper configuration
for development, testing, or production-like environments.

Usage:
    python scripts/start_server.py --help
    python scripts/start_server.py dev
    python scripts/start_server.py test
    python scripts/start_server.py prod
"""

import argparse
import os
import sys
import subprocess
from typing import Dict, Any


class ServerStarter:
    """Server startup management."""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def start_development_server(self, args: argparse.Namespace) -> int:
        """Start development server with hot reload."""
        print("Starting SelfOS Backend API - Development Mode")
        print("=" * 50)
        
        cmd = [
            sys.executable, "-m", "uvicorn", "main:app",
            "--reload",
            "--host", args.host,
            "--port", str(args.port),
            "--log-level", "info" if not args.debug else "debug"
        ]
        
        env = self._get_development_env(args)
        
        print(f"Server URL: http://{args.host}:{args.port}")
        print(f"API Docs: http://{args.host}:{args.port}/docs")
        print(f"Health Check: http://{args.host}:{args.port}/health")
        print("Press Ctrl+C to stop\n")
        
        self._print_env_info(env)
        
        return subprocess.run(cmd, cwd=self.base_dir, env=env).returncode
    
    def start_test_server(self, args: argparse.Namespace) -> int:
        """Start server optimized for testing."""
        print("Starting SelfOS Backend API - Test Mode")
        print("=" * 50)
        
        cmd = [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", args.host,
            "--port", str(args.port),
            "--log-level", "warning"
        ]
        
        env = self._get_test_env(args)
        
        print(f"Test Server URL: http://{args.host}:{args.port}")
        print("Optimized for testing (minimal logging, mock AI, in-memory DB)")
        print("Press Ctrl+C to stop\n")
        
        return subprocess.run(cmd, cwd=self.base_dir, env=env).returncode
    
    def start_production_server(self, args: argparse.Namespace) -> int:
        """Start production-like server."""
        print("Starting SelfOS Backend API - Production Mode")
        print("=" * 50)
        print("WARNING: This is for local production testing only!")
        print("Use proper WSGI server (gunicorn) for real production")
        print()
        
        cmd = [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", args.host,
            "--port", str(args.port),
            "--workers", str(args.workers),
            "--log-level", "info"
        ]
        
        env = self._get_production_env(args)
        
        print(f"Production Server URL: http://{args.host}:{args.port}")
        print(f"Workers: {args.workers}")
        print("Press Ctrl+C to stop\n")
        
        self._print_env_info(env)
        
        return subprocess.run(cmd, cwd=self.base_dir, env=env).returncode
    
    def _get_development_env(self, args: argparse.Namespace) -> Dict[str, str]:
        """Get environment variables for development."""
        env = os.environ.copy()
        
        # Development defaults
        dev_env = {
            "DATABASE_URL": "sqlite:///./selfos_dev.db",
            "SECRET_KEY": "dev-secret-key-change-in-production",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG" if args.debug else "INFO",
            
            # AI Configuration
            "AI_PROVIDER": "local",  # Use mock for development
            "AI_ENABLE_CACHING": "true",
            "AI_CACHE_TTL": "300",  # 5 minutes
            "AI_MAX_RETRIES": "2",
            "AI_RATE_LIMIT": "30",
            
            # Memory Service
            "MEMORY_VECTOR_STORE": "memory",
            "MEMORY_SIMILARITY_THRESHOLD": "0.7",
            
            # Rate Limiting (relaxed for development)
            "RATE_LIMIT_REQUESTS_PER_MINUTE": "100",
            "RATE_LIMIT_REQUESTS_PER_HOUR": "5000",
            "RATE_LIMIT_BURST_LIMIT": "20"
        }
        
        # Override with any environment variables from .env file
        env_file = os.path.join(self.base_dir, ".env")
        if os.path.exists(env_file):
            print(f"Loading environment from {env_file}")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        dev_env[key.strip()] = value.strip()
        
        env.update(dev_env)
        return env
    
    def _get_test_env(self, args: argparse.Namespace) -> Dict[str, str]:
        """Get environment variables for testing."""
        env = os.environ.copy()
        
        test_env = {
            "TESTING": "true",
            "DATABASE_URL": "sqlite:///./selfos_test.db",
            "SECRET_KEY": "test-secret-key-do-not-use-in-production",
            "DEBUG": "false",
            "LOG_LEVEL": "WARNING",
            
            # AI Configuration (mock only)
            "AI_PROVIDER": "local",
            "AI_ENABLE_CACHING": "false",
            "AI_MAX_RETRIES": "1",
            "AI_RATE_LIMIT": "1000",
            
            # Memory Service (in-memory only)
            "MEMORY_VECTOR_STORE": "memory",
            "MEMORY_SIMILARITY_THRESHOLD": "0.5",
            
            # Relaxed rate limiting for tests
            "RATE_LIMIT_REQUESTS_PER_MINUTE": "10000",
            "RATE_LIMIT_REQUESTS_PER_HOUR": "100000",
            "RATE_LIMIT_BURST_LIMIT": "1000"
        }
        
        env.update(test_env)
        return env
    
    def _get_production_env(self, args: argparse.Namespace) -> Dict[str, str]:
        """Get environment variables for production-like setup."""
        env = os.environ.copy()
        
        # Check for required production environment variables
        required_vars = ["SECRET_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"WARNING: Missing required environment variables: {missing_vars}")
            print("Using development defaults - NOT suitable for real production!")
        
        prod_env = {
            "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///./selfos_prod.db"),
            "SECRET_KEY": os.getenv("SECRET_KEY", "prod-secret-key-CHANGE-THIS"),
            "DEBUG": "false",
            "LOG_LEVEL": "INFO",
            
            # AI Configuration
            "AI_PROVIDER": os.getenv("AI_PROVIDER", "openai"),
            "AI_ENABLE_CACHING": "true",
            "AI_CACHE_TTL": "3600",  # 1 hour
            "AI_MAX_RETRIES": "3",
            "AI_RATE_LIMIT": "100",
            "AI_ENABLE_COST_TRACKING": "true",
            
            # Memory Service
            "MEMORY_VECTOR_STORE": os.getenv("MEMORY_VECTOR_STORE", "pinecone"),
            "MEMORY_SIMILARITY_THRESHOLD": "0.7",
            
            # Production rate limiting
            "RATE_LIMIT_REQUESTS_PER_MINUTE": "60",
            "RATE_LIMIT_REQUESTS_PER_HOUR": "1000",
            "RATE_LIMIT_BURST_LIMIT": "10"
        }
        
        env.update(prod_env)
        return env
    
    def _print_env_info(self, env: Dict[str, str]):
        """Print relevant environment information."""
        important_vars = [
            "DATABASE_URL", "AI_PROVIDER", "MEMORY_VECTOR_STORE",
            "RATE_LIMIT_REQUESTS_PER_MINUTE", "DEBUG"
        ]
        
        print("Configuration:")
        for var in important_vars:
            value = env.get(var, "Not set")
            # Hide sensitive information
            if "SECRET" in var or "KEY" in var:
                value = "***" if value != "Not set" else value
            print(f"  {var}: {value}")
        print()
    
    def check_dependencies(self):
        """Check if required dependencies are available."""
        print("Checking dependencies...")
        
        # Check Python packages
        required_packages = ["fastapi", "uvicorn", "sqlalchemy", "pydantic"]
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"ERROR: Missing required packages: {missing_packages}")
            print("Install with: pip install -r requirements.txt")
            return False
        
        print("✅ All required packages available")
        
        # Check database directory
        db_dir = os.path.dirname(os.path.join(self.base_dir, "selfos.db"))
        if not os.path.exists(db_dir):
            print(f"Creating database directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
        
        print("✅ Database directory ready")
        return True
    
    def show_server_info(self):
        """Show information about server startup options."""
        print("SelfOS Backend API Server Information")
        print("=" * 40)
        
        print("\nAvailable startup modes:")
        print("  dev  - Development mode with hot reload and debug logging")
        print("  test - Test mode with minimal logging and mock services")
        print("  prod - Production-like mode (local testing only)")
        
        print("\nKey features per mode:")
        print("  Development:")
        print("    - Hot reload on file changes")
        print("    - Debug logging enabled")
        print("    - Mock AI provider (no API costs)")
        print("    - In-memory vector store")
        print("    - Relaxed rate limiting")
        
        print("  Test:")
        print("    - Minimal logging (warnings only)")
        print("    - Mock AI provider")
        print("    - In-memory vector store")
        print("    - No rate limiting")
        print("    - Separate test database")
        
        print("  Production:")
        print("    - Multiple worker processes")
        print("    - Real AI providers (if configured)")
        print("    - Real vector store (if configured)")
        print("    - Production rate limiting")
        print("    - Requires proper environment setup")
        
        print("\nEnvironment configuration:")
        print("  Create .env file for development overrides")
        print("  Set environment variables for production")
        print("  See docs/LOCAL_DEVELOPMENT_SETUP.md for details")


def main():
    parser = argparse.ArgumentParser(
        description="SelfOS Backend API Server Starter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start_server.py dev                    # Start development server
  python scripts/start_server.py dev --debug            # With debug logging
  python scripts/start_server.py test --port 8001       # Test server on port 8001
  python scripts/start_server.py prod --workers 4       # Production with 4 workers
  python scripts/start_server.py info                   # Show server information
        """
    )
    
    parser.add_argument(
        "mode",
        choices=["dev", "test", "prod", "info"],
        help="Server startup mode"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (prod mode only, default: 1)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging (dev mode only)"
    )
    
    parser.add_argument(
        "--no-deps-check",
        action="store_true",
        help="Skip dependency checking"
    )
    
    args = parser.parse_args()
    
    starter = ServerStarter()
    
    if args.mode == "info":
        starter.show_server_info()
        return 0
    
    # Check dependencies unless skipped
    if not args.no_deps_check and not starter.check_dependencies():
        return 1
    
    # Start server
    start_methods = {
        "dev": starter.start_development_server,
        "test": starter.start_test_server,
        "prod": starter.start_production_server
    }
    
    try:
        return start_methods[args.mode](args)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())