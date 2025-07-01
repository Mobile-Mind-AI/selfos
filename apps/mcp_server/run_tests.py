#!/usr/bin/env python3
"""
Test runner for SelfOS MCP Server

Runs the complete test suite for the MCP server implementation.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests(test_type="all", verbose=True, coverage=False):
    """
    Run tests for the MCP server.
    
    Args:
        test_type: Type of tests to run ("all", "unit", "integration")
        verbose: Whether to run in verbose mode
        coverage: Whether to generate coverage report
    """
    
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test selection
    if test_type == "unit":
        cmd.extend(["-m", "not integration"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    # Add test directory
    cmd.append("tests/")
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Please install it with: pip install pytest pytest-asyncio")
        return False


def check_dependencies():
    """Check if required test dependencies are installed."""
    required_packages = ["pytest", "pytest-asyncio"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)}")
        return False
    
    return True


def main():
    """Main entry point for test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run MCP Server tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration"], 
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Run in quiet mode"
    )
    
    args = parser.parse_args()
    
    print("🧪 SelfOS MCP Server Test Runner")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Run tests
    success = run_tests(
        test_type=args.type,
        verbose=not args.quiet,
        coverage=args.coverage
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()