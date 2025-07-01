# SelfOS MCP Server

Model Context Protocol (MCP) server implementation for SelfOS, providing standardized AI integration with user data and APIs.

## Overview

The SelfOS MCP Server implements Anthropic's Model Context Protocol to provide secure, standardized access to SelfOS functionality for AI agents and clients. This enables sophisticated AI interactions with user goals, projects, tasks, and other personal data.

## Quick Start

### Via Docker (Recommended)
```bash
# From project root
docker-compose up --build mcp-server
# Access: http://localhost:8001
```

### Local Development
```bash
cd apps/mcp_server
python test_server.py            # Test functionality
python fastapi_integration.py    # Start web server
python cli.py --transport stdio  # CLI mode for AI agents
```

### Testing
```bash
python run_tests.py              # 37 comprehensive tests
python run_tests.py --coverage   # With coverage report
```

## Features

✅ **Complete Goals API** (6 tools)  
✅ **Security & Authentication** (Firebase + API keys)  
✅ **Multiple Transports** (stdio, WebSocket, SSE)  
✅ **Comprehensive Testing** (37 tests)  
🚧 **Projects/Tasks APIs** (framework ready)  
🚧 **AI Tools** (goal decomposition, suggestions)  

## Documentation

📋 **[Complete Documentation](../../docs/MCP_SERVER.md)** - Full API reference and guides  
🚀 **[Quick Reference](../../docs/QUICK_REFERENCE.md)** - Essential commands  
👨‍💻 **[Developer Guide](../../CLAUDE.md)** - Development instructions

---

**Ready to integrate AI agents with SelfOS? Check the complete documentation above!**