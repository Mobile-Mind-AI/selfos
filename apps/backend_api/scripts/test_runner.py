#!/usr/bin/env python3
"""
SelfOS Test Runner

Comprehensive test runner script that can execute tests against different environments:
- Local test client (default, fast)
- Live local server (requires running server)
- Different AI providers
- Different configurations

Usage:
    python scripts/test_runner.py --help
    python scripts/test_runner.py unit
    python scripts/test_runner.py integration
    python scripts/test_runner.py chat --live-server
    python scripts/test_runner.py all --ai-provider openai
"""

import argparse
import os
import sys
import subprocess
import time
import requests
from typing import List, Optional
import json


class TestRunner:
    """Main test runner class."""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_root = os.path.dirname(os.path.dirname(self.base_dir))
        
    def run_command(self, cmd: List[str], env: Optional[dict] = None) -> int:
        """Run a command and return the exit code."""
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        print(f"Running: {' '.join(cmd)}")
        if env:
            print(f"Environment: {env}")
        
        result = subprocess.run(cmd, cwd=self.base_dir, env=full_env)
        return result.returncode
    
    def check_server_health(self, url: str, timeout: int = 30) -> bool:
        """Check if server is running and healthy."""
        print(f"Checking server health at {url}")
        
        for i in range(timeout):
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"Server is healthy: {health_data.get('status', 'unknown')}")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            if i < timeout - 1:
                print(f"Waiting for server... ({i+1}/{timeout})")
                time.sleep(1)
        
        print(f"Server not available at {url}")
        return False
    
    def start_test_server(self, port: int = 8001) -> subprocess.Popen:
        """Start a test server for live testing."""
        print(f"Starting test server on port {port}")
        
        # Use a different port for testing to avoid conflicts
        cmd = [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--log-level", "warning"
        ]
        
        env = {
            "TESTING": "true",
            "DATABASE_URL": "sqlite:///./test_live_server.db",
            "AI_PROVIDER": "local",
            "RATE_LIMIT_REQUESTS_PER_MINUTE": "1000"
        }
        
        process = subprocess.Popen(
            cmd, 
            cwd=self.base_dir,
            env={**os.environ, **env},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        server_url = f"http://localhost:{port}"
        if self.check_server_health(server_url, timeout=15):
            return process
        else:
            process.terminate()
            raise RuntimeError(f"Failed to start test server on port {port}")
    
    def run_unit_tests(self, args: argparse.Namespace) -> int:
        """Run unit tests."""
        cmd = ["python", "-m", "pytest", "tests/unit/", "-v"]
        
        if args.coverage:
            cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
        
        if args.verbose:
            cmd.append("-s")
        
        if args.fast:
            cmd.extend(["-x", "--tb=short"])
        
        env = self._build_test_env(args)
        return self.run_command(cmd, env)
    
    def run_integration_tests(self, args: argparse.Namespace) -> int:
        """Run integration tests."""
        cmd = ["python", "-m", "pytest", "tests/integration/", "-v"]
        
        if args.coverage:
            cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
        
        if args.verbose:
            cmd.append("-s")
        
        if args.fast:
            cmd.extend(["-x", "--tb=short"])
        
        # Exclude slow tests by default unless specifically requested
        if not args.include_slow:
            cmd.extend(["-m", "not slow"])
        
        env = self._build_test_env(args)
        
        # Handle live server testing
        server_process = None
        try:
            if args.live_server:
                if args.server_url:
                    # Use external server
                    if not self.check_server_health(args.server_url):
                        return 1
                    env["TEST_SERVER_URL"] = args.server_url
                else:
                    # Start our own test server
                    server_process = self.start_test_server()
                    env["TEST_SERVER_URL"] = "http://localhost:8001"
            
            return self.run_command(cmd, env)
            
        finally:
            if server_process:
                print("Stopping test server")
                server_process.terminate()
                server_process.wait()
    
    def run_chat_tests(self, args: argparse.Namespace) -> int:
        """Run chat simulation tests."""
        cmd = [
            "python", "-m", "pytest", 
            "tests/integration/test_chat_simulation.py",
            "tests/integration/test_advanced_chat_scenarios.py",
            "-v"
        ]
        
        if args.verbose:
            cmd.append("-s")
        
        if args.fast:
            cmd.extend(["-x", "--tb=short"])
        
        # Exclude slow tests unless requested
        if not args.include_slow:
            cmd.extend(["-m", "not slow"])
        
        env = self._build_test_env(args)
        
        # Handle live server for chat tests
        server_process = None
        try:
            if args.live_server:
                if args.server_url:
                    if not self.check_server_health(args.server_url):
                        return 1
                    env["TEST_SERVER_URL"] = args.server_url
                else:
                    server_process = self.start_test_server()
                    env["TEST_SERVER_URL"] = "http://localhost:8001"
            
            return self.run_command(cmd, env)
            
        finally:
            if server_process:
                print("Stopping test server")
                server_process.terminate()
                server_process.wait()
    
    def run_ai_tests(self, args: argparse.Namespace) -> int:
        """Run AI-specific tests."""
        cmd = [
            "python", "-m", "pytest", 
            "-m", "ai",
            "-v"
        ]
        
        if args.verbose:
            cmd.append("-s")
        
        env = self._build_test_env(args)
        
        # AI tests may need special handling
        if args.ai_provider != "local":
            print(f"Warning: Using real AI provider '{args.ai_provider}' - this may incur costs!")
            confirmation = input("Continue? (y/N): ")
            if confirmation.lower() != 'y':
                print("Cancelled")
                return 0
        
        return self.run_command(cmd, env)
    
    def run_all_tests(self, args: argparse.Namespace) -> int:
        """Run all tests."""
        cmd = ["python", "-m", "pytest", "-v"]
        
        if args.coverage:
            cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
        
        if args.verbose:
            cmd.append("-s")
        
        if args.fast:
            cmd.extend(["-x", "--tb=short"])
        
        # Exclude slow tests unless requested
        if not args.include_slow:
            cmd.extend(["-m", "not slow"])
        
        env = self._build_test_env(args)
        
        # Handle live server testing
        server_process = None
        try:
            if args.live_server:
                if args.server_url:
                    if not self.check_server_health(args.server_url):
                        return 1
                    env["TEST_SERVER_URL"] = args.server_url
                else:
                    server_process = self.start_test_server()
                    env["TEST_SERVER_URL"] = "http://localhost:8001"
            
            return self.run_command(cmd, env)
            
        finally:
            if server_process:
                print("Stopping test server")
                server_process.terminate()
                server_process.wait()
    
    def run_performance_tests(self, args: argparse.Namespace) -> int:
        """Run performance and stress tests."""
        cmd = [
            "python", "-m", "pytest",
            "-m", "slow",
            "-v", "--tb=short"
        ]
        
        if args.verbose:
            cmd.append("-s")
        
        env = self._build_test_env(args)
        return self.run_command(cmd, env)
    
    def _build_test_env(self, args: argparse.Namespace) -> dict:
        """Build environment variables for testing."""
        env = {
            "TESTING": "true",
            "PYTEST_CURRENT_TEST": "true",
            "AI_PROVIDER": args.ai_provider,
            "MEMORY_VECTOR_STORE": args.memory_store,
            "RATE_LIMIT_REQUESTS_PER_MINUTE": "10000"
        }
        
        # AI provider specific settings
        if args.ai_provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                print("Warning: OPENAI_API_KEY not set")
            env["AI_ENABLE_CACHING"] = "true"  # Save costs
        elif args.ai_provider == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                print("Warning: ANTHROPIC_API_KEY not set")
            env["AI_ENABLE_CACHING"] = "true"  # Save costs
        else:
            env["AI_ENABLE_CACHING"] = "false"  # No need for local
        
        # Memory store specific settings
        if args.memory_store == "pinecone":
            if not os.getenv("PINECONE_API_KEY"):
                print("Warning: PINECONE_API_KEY not set")
        
        # Custom environment variables
        if args.env:
            for env_var in args.env:
                if "=" in env_var:
                    key, value = env_var.split("=", 1)
                    env[key] = value
                else:
                    print(f"Warning: Invalid environment variable format: {env_var}")
        
        return env
    
    def show_test_info(self):
        """Show information about available tests."""
        print("SelfOS Test Suite Information")
        print("=" * 40)
        
        # Count test files
        test_files = {
            "Unit tests": [],
            "Integration tests": [],
            "Chat simulation tests": []
        }
        
        unit_dir = os.path.join(self.base_dir, "tests", "unit")
        integration_dir = os.path.join(self.base_dir, "tests", "integration")
        
        if os.path.exists(unit_dir):
            test_files["Unit tests"] = [f for f in os.listdir(unit_dir) if f.startswith("test_") and f.endswith(".py")]
        
        if os.path.exists(integration_dir):
            all_integration = [f for f in os.listdir(integration_dir) if f.startswith("test_") and f.endswith(".py")]
            chat_tests = [f for f in all_integration if "chat" in f]
            other_integration = [f for f in all_integration if f not in chat_tests]
            
            test_files["Integration tests"] = other_integration
            test_files["Chat simulation tests"] = chat_tests
        
        for category, files in test_files.items():
            print(f"\n{category}: {len(files)} files")
            for file in sorted(files):
                print(f"  - {file}")
        
        print(f"\nTest markers available:")
        print("  - unit: Unit tests (fast, isolated)")
        print("  - integration: Integration tests")
        print("  - ai: AI-related tests")
        print("  - memory: Memory service tests")
        print("  - chat: Chat simulation tests")
        print("  - slow: Performance/stress tests")
        print("  - live: Live server tests")


def main():
    parser = argparse.ArgumentParser(
        description="SelfOS Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_runner.py unit                    # Run unit tests
  python scripts/test_runner.py integration             # Run integration tests
  python scripts/test_runner.py chat --verbose          # Run chat tests with output
  python scripts/test_runner.py all --coverage          # Run all tests with coverage
  python scripts/test_runner.py integration --live-server  # Test against live server
  python scripts/test_runner.py ai --ai-provider openai # Test with real OpenAI
  python scripts/test_runner.py performance             # Run stress tests
  python scripts/test_runner.py info                    # Show test information
        """
    )
    
    # Test type selection
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "chat", "ai", "all", "performance", "info"],
        help="Type of tests to run"
    )
    
    # Server options
    parser.add_argument(
        "--live-server",
        action="store_true",
        help="Run tests against a live server (starts one if needed)"
    )
    
    parser.add_argument(
        "--server-url",
        help="URL of live server to test against (e.g., http://localhost:8000)"
    )
    
    # AI options
    parser.add_argument(
        "--ai-provider",
        choices=["local", "openai", "anthropic"],
        default="local",
        help="AI provider to use for testing (default: local/mock)"
    )
    
    parser.add_argument(
        "--memory-store",
        choices=["memory", "pinecone"],
        default="memory",
        help="Memory store to use for testing (default: in-memory)"
    )
    
    # Test options
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage reporting"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output (show print statements)"
    )
    
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode (stop on first failure)"
    )
    
    parser.add_argument(
        "--include-slow",
        action="store_true",
        help="Include slow/performance tests"
    )
    
    parser.add_argument(
        "--env",
        action="append",
        help="Additional environment variables (KEY=VALUE)"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.test_type == "info":
        runner.show_test_info()
        return 0
    
    # Validate arguments
    if args.server_url and not args.live_server:
        print("Warning: --server-url specified but --live-server not enabled")
    
    # Run tests
    test_methods = {
        "unit": runner.run_unit_tests,
        "integration": runner.run_integration_tests,
        "chat": runner.run_chat_tests,
        "ai": runner.run_ai_tests,
        "all": runner.run_all_tests,
        "performance": runner.run_performance_tests
    }
    
    exit_code = test_methods[args.test_type](args)
    
    if exit_code == 0:
        print(f"\n✅ {args.test_type.title()} tests passed!")
    else:
        print(f"\n❌ {args.test_type.title()} tests failed!")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())