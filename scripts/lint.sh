#!/bin/bash
# Linting and formatting script for SelfOS project
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
RUN_FORMAT=true
RUN_LINT=true
RUN_SECURITY=false
RUN_TYPE_CHECK=false
AUTO_FIX=false
CHECK_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --format-only)
            RUN_FORMAT=true
            RUN_LINT=false
            RUN_SECURITY=false
            RUN_TYPE_CHECK=false
            shift
            ;;
        --lint-only)
            RUN_FORMAT=false
            RUN_LINT=true
            RUN_SECURITY=false
            RUN_TYPE_CHECK=false
            shift
            ;;
        --security)
            RUN_SECURITY=true
            shift
            ;;
        --type-check|--mypy)
            RUN_TYPE_CHECK=true
            shift
            ;;
        --all)
            RUN_FORMAT=true
            RUN_LINT=true
            RUN_SECURITY=true
            RUN_TYPE_CHECK=true
            shift
            ;;
        --fix)
            AUTO_FIX=true
            shift
            ;;
        --check)
            CHECK_ONLY=true
            AUTO_FIX=false
            shift
            ;;
        --help|-h)
            echo "SelfOS Linting and Formatting Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --format-only    Run only formatting tools (black, isort)"
            echo "  --lint-only      Run only linting tools (ruff)"
            echo "  --security       Include security checks (bandit)"
            echo "  --type-check     Include type checking (mypy)"
            echo "  --all            Run all tools (format, lint, security, type-check)"
            echo "  --fix            Automatically fix issues where possible"
            echo "  --check          Check mode only (don't modify files)"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                # Run formatting and linting"
            echo "  $0 --all          # Run all checks including security and types"
            echo "  $0 --check        # Check code quality without modifying files"
            echo "  $0 --fix          # Automatically fix formatting and linting issues"
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

# Track overall success
OVERALL_SUCCESS=true

print_status "🔧 Running SelfOS code quality checks..."
echo "Configuration:"
echo "  Format: $RUN_FORMAT"
echo "  Lint: $RUN_LINT"
echo "  Security: $RUN_SECURITY"
echo "  Type Check: $RUN_TYPE_CHECK"
echo "  Auto Fix: $AUTO_FIX"
echo "  Check Only: $CHECK_ONLY"
echo ""

# Code formatting with Black
if [[ "$RUN_FORMAT" == "true" ]]; then
    print_status "🎨 Running Black (code formatter)..."

    BLACK_ARGS="--line-length 88"
    if [[ "$CHECK_ONLY" == "true" ]]; then
        BLACK_ARGS="$BLACK_ARGS --check --diff"
    fi

    if black $BLACK_ARGS apps/; then
        print_success "✅ Black formatting passed"
    else
        print_error "❌ Black formatting issues found"
        OVERALL_SUCCESS=false
    fi
    echo ""
fi

# Import sorting with isort
if [[ "$RUN_FORMAT" == "true" ]]; then
    print_status "📦 Running isort (import sorting)..."

    ISORT_ARGS="--profile black --line-length 88"
    if [[ "$CHECK_ONLY" == "true" ]]; then
        ISORT_ARGS="$ISORT_ARGS --check-only --diff"
    fi

    if isort $ISORT_ARGS apps/; then
        print_success "✅ isort import sorting passed"
    else
        print_error "❌ isort import sorting issues found"
        OVERALL_SUCCESS=false
    fi
    echo ""
fi

# Linting with ruff
if [[ "$RUN_LINT" == "true" ]]; then
    print_status "🔍 Running Ruff (linter)..."

    RUFF_ARGS=""
    if [[ "$AUTO_FIX" == "true" && "$CHECK_ONLY" != "true" ]]; then
        RUFF_ARGS="--fix"
    fi

    if ruff check $RUFF_ARGS apps/; then
        print_success "✅ Ruff linting passed"
    else
        print_error "❌ Ruff linting issues found"
        OVERALL_SUCCESS=false
    fi
    echo ""
fi

# Security scanning with bandit
if [[ "$RUN_SECURITY" == "true" ]]; then
    print_status "🔒 Running Bandit (security scanner)..."

    if command -v bandit >/dev/null 2>&1; then
        if bandit -r apps/ --skip B101 -f screen; then
            print_success "✅ Bandit security scan passed"
        else
            print_warning "⚠️ Bandit security scan found issues"
            # Don't fail overall for security warnings
        fi
    else
        print_warning "⚠️ Bandit not installed, skipping security scan"
    fi
    echo ""
fi

# Type checking with mypy
if [[ "$RUN_TYPE_CHECK" == "true" ]]; then
    print_status "🏷️ Running MyPy (type checker)..."

    if command -v mypy >/dev/null 2>&1; then
        # Run mypy on specific directories to avoid overwhelming output
        MYPY_SUCCESS=true
        for dir in apps/backend_api/models apps/backend_api/services apps/backend_api/routers apps/mcp_server/tools; do
            if [[ -d "$dir" ]]; then
                print_status "  Checking $dir..."
                if ! mypy --ignore-missing-imports --scripts-are-modules "$dir" 2>/dev/null; then
                    MYPY_SUCCESS=false
                fi
            fi
        done

        if [[ "$MYPY_SUCCESS" == "true" ]]; then
            print_success "✅ MyPy type checking passed"
        else
            print_warning "⚠️ MyPy type checking found issues"
            # Don't fail overall for type warnings in early development
        fi
    else
        print_warning "⚠️ MyPy not installed, skipping type checking"
    fi
    echo ""
fi

# Summary
echo "=========================================="
echo "🏁 Code Quality Summary"
echo "=========================================="

if [[ "$OVERALL_SUCCESS" == "true" ]]; then
    print_success "🎉 All required checks passed!"
    echo ""
    print_status "💡 Pro tips:"
    echo "  - Run this script before committing: ./scripts/lint.sh"
    echo "  - Use --all flag for comprehensive checks: ./scripts/lint.sh --all"
    echo "  - Setup pre-commit hooks: pre-commit install"
    echo "  - Format on save in your IDE for best experience"
    exit 0
else
    print_error "❌ Some code quality checks failed"
    echo ""
    print_status "🔧 Quick fixes:"
    echo "  - Auto-fix formatting: ./scripts/lint.sh --fix"
    echo "  - Run pre-commit on all files: pre-commit run --all-files"
    echo "  - Check specific issues with: ./scripts/lint.sh --check"
    exit 1
fi
