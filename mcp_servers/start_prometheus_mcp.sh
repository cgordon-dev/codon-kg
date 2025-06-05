#!/bin/bash
# Start Prometheus MCP Server on port 8000

set -e

# Load environment variables if .env exists
if [ -f "../agents/.env" ]; then
    echo "Loading environment from ../agents/.env"
    export $(cat ../agents/.env | grep -v '^#' | xargs)
fi

# Set default values if not provided
export PROMETHEUS_URL=${PROMETHEUS_URL:-"http://localhost:9090"}
export MCP_SERVER_PORT=${MCP_SERVER_PORT:-"8000"}
export MCP_SERVER_NAME=${MCP_SERVER_NAME:-"prometheus-mcp-server"}

echo "Starting Prometheus MCP Server..."
echo "Prometheus URL: $PROMETHEUS_URL"
echo "Server Port: $MCP_SERVER_PORT"

# Start the server
python3 prometheus_server.py