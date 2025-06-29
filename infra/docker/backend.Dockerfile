FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY apps/backend_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/backend_api /app

# Create necessary directories
RUN mkdir -p /app/logs

# Set environment variables for event system
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO
ENV EVENT_SYSTEM_ENABLED=true
ENV EVENT_TIMEOUT_SECONDS=30

# Health check for the application
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# curl is already installed above

# Create startup script
COPY apps/backend_api/startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Run the application
CMD ["/app/startup.sh"]