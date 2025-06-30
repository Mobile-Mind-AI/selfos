#!/bin/bash

# SelfOS AI Providers Setup Script
# This script installs AI provider dependencies and validates configuration

set -e

echo "🤖 Setting up SelfOS AI Providers..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Determine backend API directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")/apps/backend_api"

# Check if we can find the backend directory
if [ ! -f "$BACKEND_DIR/requirements.txt" ]; then
    print_error "Backend API directory not found at $BACKEND_DIR"
    print_info "Please run this script from the project root or adjust paths"
    exit 1
fi

cd "$BACKEND_DIR"
print_info "Working in directory: $BACKEND_DIR"

# Function to get value from .env file
get_env_value() {
    local key=$1
    local default=$2
    if [ -f ".env" ]; then
        grep "^${key}=" .env | cut -d'=' -f2- | tr -d '"' || echo "$default"
    else
        echo "$default"
    fi
}

# Function to check if value is set and not default
is_configured() {
    local value=$1
    local default_patterns=("your_.*_key_here" "not set" "" "your-.*-key-here")
    
    for pattern in "${default_patterns[@]}"; do
        if [[ "$value" =~ $pattern ]]; then
            return 1
        fi
    done
    return 0
}

# Install AI provider dependencies
echo "📦 Installing AI provider dependencies..."
pip install openai>=1.0.0 anthropic>=0.18.0

print_status "AI provider packages installed successfully"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_info "You need to create a .env file. Use .env.example as a template:"
    print_info "cp .env.example .env"
    exit 1
else
    print_status ".env file found"
fi

echo
echo "🔍 Validating current configuration..."

# Read current configuration
AI_PROVIDER=$(get_env_value "AI_PROVIDER" "not set")
OPENAI_API_KEY=$(get_env_value "OPENAI_API_KEY" "not set")
ANTHROPIC_API_KEY=$(get_env_value "ANTHROPIC_API_KEY" "not set")
AI_ENABLE_CACHING=$(get_env_value "AI_ENABLE_CACHING" "not set")
AI_CACHE_TTL=$(get_env_value "AI_CACHE_TTL" "not set")
AI_MAX_RETRIES=$(get_env_value "AI_MAX_RETRIES" "not set")
AI_RATE_LIMIT=$(get_env_value "AI_RATE_LIMIT" "not set")
MEMORY_VECTOR_STORE=$(get_env_value "MEMORY_VECTOR_STORE" "not set")

# Validate AI Provider
echo "📊 Current AI Configuration:"
echo "   AI_PROVIDER: $AI_PROVIDER"

if [ "$AI_PROVIDER" = "not set" ]; then
    print_error "AI_PROVIDER not configured"
elif [ "$AI_PROVIDER" = "openai" ]; then
    print_status "Using OpenAI provider"
    if is_configured "$OPENAI_API_KEY"; then
        print_status "OpenAI API key is configured"
    else
        print_error "OpenAI API key not configured"
        echo "   Set OPENAI_API_KEY in .env file"
    fi
elif [ "$AI_PROVIDER" = "anthropic" ]; then
    print_status "Using Anthropic provider"
    if is_configured "$ANTHROPIC_API_KEY"; then
        print_status "Anthropic API key is configured"
    else
        print_error "Anthropic API key not configured"
        echo "   Set ANTHROPIC_API_KEY in .env file"
    fi
elif [ "$AI_PROVIDER" = "local" ]; then
    print_status "Using local mock provider (no API key required)"
else
    print_warning "Unknown AI provider: $AI_PROVIDER"
    print_info "Valid options: openai, anthropic, local"
fi

# Check other AI settings
echo
echo "⚙️  AI Engine Settings:"
[ "$AI_ENABLE_CACHING" != "not set" ] && print_status "Caching: $AI_ENABLE_CACHING" || print_warning "AI_ENABLE_CACHING not set"
[ "$AI_CACHE_TTL" != "not set" ] && print_status "Cache TTL: $AI_CACHE_TTL seconds" || print_warning "AI_CACHE_TTL not set"
[ "$AI_MAX_RETRIES" != "not set" ] && print_status "Max retries: $AI_MAX_RETRIES" || print_warning "AI_MAX_RETRIES not set"
[ "$AI_RATE_LIMIT" != "not set" ] && print_status "Rate limit: $AI_RATE_LIMIT requests/min" || print_warning "AI_RATE_LIMIT not set"

# Check memory configuration
echo
echo "🧠 Memory Configuration:"
[ "$MEMORY_VECTOR_STORE" != "not set" ] && print_status "Vector store: $MEMORY_VECTOR_STORE" || print_warning "MEMORY_VECTOR_STORE not set"

# Check for missing required settings
missing_configs=()
if [ "$AI_PROVIDER" = "not set" ]; then
    missing_configs+=("AI_PROVIDER")
fi
if [ "$AI_PROVIDER" = "openai" ] && ! is_configured "$OPENAI_API_KEY"; then
    missing_configs+=("OPENAI_API_KEY")
fi
if [ "$AI_PROVIDER" = "anthropic" ] && ! is_configured "$ANTHROPIC_API_KEY"; then
    missing_configs+=("ANTHROPIC_API_KEY")
fi

if [ ${#missing_configs[@]} -gt 0 ]; then
    echo
    print_error "Missing required configurations:"
    for config in "${missing_configs[@]}"; do
        echo "   - $config"
    done
    echo
    print_info "Please update your .env file with the missing configurations"
    exit 1
fi

# Verify installation
echo
echo "🔍 Verifying AI provider installations..."

python3 -c "
import sys
try:
    import openai
    print('✓ OpenAI package installed successfully')
except ImportError:
    print('✗ OpenAI package installation failed')
    sys.exit(1)

try:
    import anthropic
    print('✓ Anthropic package installed successfully')
except ImportError:
    print('✗ Anthropic package installation failed')
    sys.exit(1)

print('✓ All AI providers installed successfully')
"

echo
echo "🎉 Setup complete!"
echo
echo "📋 Next steps:"
echo "1. Edit the .env file to configure your AI providers:"
echo "   - Set AI_PROVIDER to 'openai', 'anthropic', or 'local'"
echo "   - Add your API keys for the providers you want to use"
echo
echo "2. Example configurations:"
echo
echo "   For OpenAI:"
echo "   AI_PROVIDER=openai"
echo "   OPENAI_API_KEY=sk-your-key-here"
echo
echo "   For Anthropic:"
echo "   AI_PROVIDER=anthropic"
echo "   ANTHROPIC_API_KEY=your-claude-key-here"
echo
echo "   For Local/Mock (testing):"
echo "   AI_PROVIDER=local"
echo
echo "3. Restart your server to apply changes"
echo
echo "4. Test the configuration with:"
echo "   curl http://localhost:8000/api/ai/health"
echo

echo
echo "🎉 Configuration validation complete!"

# Provide recommendations based on current setup
echo
echo "💡 Recommendations:"

if [ "$AI_PROVIDER" = "openai" ]; then
    echo "   - You're using OpenAI. Consider enabling caching to reduce costs"
    echo "   - Monitor your API usage at https://platform.openai.com/usage"
    echo "   - For production, consider setting AI_CACHE_TTL=3600 or higher"
elif [ "$AI_PROVIDER" = "anthropic" ]; then
    echo "   - You're using Anthropic Claude. Great choice for reasoning tasks"
    echo "   - Monitor your API usage at https://console.anthropic.com"
    echo "   - Claude handles longer contexts well, good for complex conversations"
elif [ "$AI_PROVIDER" = "local" ]; then
    echo "   - You're using local mock provider - perfect for development"
    echo "   - Switch to openai or anthropic for production use"
    echo "   - No API costs, but responses are simulated"
fi

echo
echo "🚀 Next steps:"
echo "1. Restart your server to apply any configuration changes"
echo "2. Test the AI endpoints:"
echo "   curl http://localhost:8000/api/ai/health"
echo "3. Try a chat request:"
echo "   curl -X POST http://localhost:8000/api/ai/chat \\"
echo "     -H 'Authorization: Bearer your-token' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": \"Hello, help me set a goal\"}'"

echo
echo "📚 For more configuration options, see:"
echo "   - .env.example for all available settings"
echo "   - AI_PROVIDERS_SETUP.md for detailed setup guide"