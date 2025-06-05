#!/bin/bash
# Start Neo4j MCP Server on port 8001

set -e

# Load environment variables if .env exists
if [ -f "../agents/.env" ]; then
    echo "Loading environment from ../agents/.env"
    export $(cat ../agents/.env | grep -v '^#' | xargs)
fi

# Set default values if not provided
export NEO4J_URI=${NEO4J_URI:-"bolt://localhost:7687"}
export NEO4J_USERNAME=${NEO4J_USERNAME:-"neo4j"}
export NEO4J_PASSWORD=${NEO4J_PASSWORD:-"password"}
export NEO4J_DATABASE=${NEO4J_DATABASE:-"neo4j"}
export MCP_SERVER_PORT=${MCP_SERVER_PORT:-"8001"}
export MCP_SERVER_NAME=${MCP_SERVER_NAME:-"neo4j-mcp-server"}

echo "Starting Neo4j MCP Server..."
echo "Neo4j URI: $NEO4J_URI"
echo "Neo4j Database: $NEO4J_DATABASE"
echo "Server Port: $MCP_SERVER_PORT"

# Start the server
python3 neo4j_server.py