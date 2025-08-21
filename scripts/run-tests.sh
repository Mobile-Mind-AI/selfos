#!/bin/bash
# Test runner script for SelfOS project
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default options
RUN_BACKEND=true
RUN_MCP=true
RUN_COVERAGE=true
PARALLEL=true
VERBOSE=false
FAIL_FAST=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only|--backend)
            RUN_BACKEND=true
            RUN_MCP=false
            shift
            ;;
        --mcp-only|--mcp)
            RUN_BACKEND=false
            RUN_MCP=true
            shift
            ;;
        --no-coverage)
            RUN_COVERAGE=false
            shift
            ;;
        --sequential)
            PARALLEL=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --fail-fast|-x)
            FAIL_FAST=true
            shift
            ;;
        --help|-h)
            echo "SelfOS Test Runner"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --backend-only, --backend    Run only backend API tests"
            echo "  --mcp-only, --mcp           Run only MCP server tests"
            echo "  --no-coverage               Skip coverage reporting"
            echo "  --sequential                Run tests sequentially (disable parallel)"
            echo "  --verbose, -v               Verbose output"
            echo "  --fail-fast, -x             Stop on first failure"
            echo "  --help, -h                  Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                          # Run all tests with coverage"
            echo "  $0 --backend-only           # Run only backend tests"
            echo "  $0 --no-coverage --verbose  # Run all tests without coverage, verbose"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warning "Virtual environment not detected. Attempting to activate..."
    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "No virtual environment found. Run ./scripts/setup-dev-environment.sh first"
        exit 1
    fi
fi

# Check if required packages are installed
if ! python -c "import pytest" 2>/dev/null; then
    print_error "pytest not found. Run ./scripts/setup-dev-environment.sh to install dependencies"
    exit 1
fi

# Build pytest command
PYTEST_ARGS="--tb=short -ra"

if [[ "$VERBOSE" == "true" ]]; then
    PYTEST_ARGS="$PYTEST_ARGS --verbose"
fi

if [[ "$FAIL_FAST" == "true" ]]; then
    PYTEST_ARGS="$PYTEST_ARGS -x"
fi

if [[ "$PARALLEL" == "true" ]]; then
    PYTEST_ARGS="$PYTEST_ARGS -n auto --dist=worksteal"
fi

if [[ "$RUN_COVERAGE" == "true" ]]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=apps --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml"
fi

# Initialize test results
BACKEND_RESULT=0
MCP_RESULT=0

print_status "🧪 Starting SelfOS test suite..."
echo "Configuration:"
echo "  Backend tests: $RUN_BACKEND"
echo "  MCP tests: $RUN_MCP"
echo "  Coverage: $RUN_COVERAGE"
echo "  Parallel: $PARALLEL"
echo ""

# Run backend API tests
if [[ "$RUN_BACKEND" == "true" ]]; then
    print_status "🔧 Running Backend API tests..."
    
    cd apps/backend_api
    
    # Setup test environment
    export $(cat .env.test 2>/dev/null | grep -v '^#' | xargs) || true
    export TESTING=true
    export PYTEST_CURRENT_TEST=true
    
    # Create dummy Firebase credentials if needed
    if [[ ! -f "/tmp/dummy-firebase.json" ]]; then
        echo '{"type": "service_account", "project_id": "test-project"}' > /tmp/dummy-firebase.json
    fi
    
    # Run the tests
    if python -m pytest tests/ $PYTEST_ARGS; then
        print_success "✅ Backend API tests passed"
        BACKEND_RESULT=0
    else
        print_error "❌ Backend API tests failed"
        BACKEND_RESULT=1
    fi
    
    cd ../..
    echo ""
fi

# Run MCP server tests
if [[ "$RUN_MCP" == "true" ]]; then
    print_status "🔗 Running MCP Server tests..."
    
    cd apps/mcp_server
    
    # Run the tests
    if python -m pytest tests/ $PYTEST_ARGS; then
        print_success "✅ MCP Server tests passed"
        MCP_RESULT=0
    else
        print_error "❌ MCP Server tests failed"
        MCP_RESULT=1
    fi
    
    cd ../..
    echo ""
fi

# Generate combined coverage report if both were run
if [[ "$RUN_COVERAGE" == "true" && "$RUN_BACKEND" == "true" && "$RUN_MCP" == "true" ]]; then
    print_status "📊 Generating combined coverage report..."
    
    # Combine coverage data
    if command -v coverage >/dev/null 2>&1; then
        coverage combine apps/backend_api/.coverage apps/mcp_server/.coverage 2>/dev/null || true
        coverage report --format=markdown > coverage-summary.md 2>/dev/null || true
        print_success "Combined coverage report generated: coverage-summary.md"
    fi
fi

# Summary
echo ""
echo "=========================================="
echo "🏁 Test Results Summary"
echo "=========================================="

TOTAL_FAILURES=0

if [[ "$RUN_BACKEND" == "true" ]]; then
    if [[ $BACKEND_RESULT -eq 0 ]]; then
        print_success "Backend API: ✅ PASSED"
    else
        print_error "Backend API: ❌ FAILED"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
fi

if [[ "$RUN_MCP" == "true" ]]; then
    if [[ $MCP_RESULT -eq 0 ]]; then
        print_success "MCP Server: ✅ PASSED"
    else
        print_error "MCP Server: ❌ FAILED"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
fi

echo ""
if [[ $TOTAL_FAILURES -eq 0 ]]; then
    print_success "🎉 All tests passed!"
    
    if [[ "$RUN_COVERAGE" == "true" ]]; then
        echo ""
        print_status "📊 Coverage reports available:"
        echo "  - HTML: htmlcov/index.html"
        echo "  - XML: coverage.xml"
        if [[ -f "coverage-summary.md" ]]; then
            echo "  - Summary: coverage-summary.md"
        fi
    fi
    
    exit 0
else
    print_error "❌ $TOTAL_FAILURES test suite(s) failed"
    exit 1
fi
