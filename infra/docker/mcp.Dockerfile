FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY apps/backend_api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend_api for database models and dependencies
COPY apps/backend_api/ /app/backend_api/

# Copy the MCP server
COPY apps/mcp_server/ /app/mcp_server/

# Set Python path to include both directories
ENV PYTHONPATH="/app/backend_api:/app/mcp_server:$PYTHONPATH"

# Change to mcp_server directory
WORKDIR /app/mcp_server

# Default command - can be overridden
CMD ["python", "cli.py", "--transport", "websocket"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import server; print('MCP server healthy')" || exit 1