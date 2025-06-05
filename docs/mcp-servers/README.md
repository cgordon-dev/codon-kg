# MCP Servers

Model Context Protocol (MCP) servers for Prometheus monitoring and Neo4j graph database integration.

## Overview

This directory contains MCP servers that provide tool capabilities to the LangChain agents:

- **Prometheus MCP Server** (Port 8000): Monitoring and metrics tools
- **Neo4j MCP Server** (Port 8001): Graph database query and analysis tools

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent Client  │────│   MCP Server    │────│  External API   │
│   (agents/)     │    │ (mcp_servers/)  │    │ (Prometheus/    │
│                 │    │                 │    │  Neo4j)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Docker (Recommended)

```bash
# Start all services including MCP servers
docker compose up -d

# Check MCP server status
docker compose ps
docker exec codon-neo4j-mcp pgrep -f "neo4j_server.py"
docker exec codon-prometheus-mcp pgrep -f "prometheus_server.py"
```

### Manual Setup

1. **Install Dependencies**:
```bash
cd mcp_servers
pip install -r requirements.txt
```

2. **Configure Environment**:
```bash
cp ../agents/.env.example ../agents/.env
# Edit .env with your Prometheus and Neo4j connection details
```

3. **Start All Servers**:
```bash
# Start both servers with process management
python3 start_mcp_servers.py
```

Or start individually:
```bash
# Terminal 1 - Prometheus MCP Server
./start_prometheus_mcp.sh

# Terminal 2 - Neo4j MCP Server  
./start_neo4j_mcp.sh
```

## Server Details

### Prometheus MCP Server (`prometheus_server.py`)

**Port**: 8000  
**Purpose**: Provides monitoring and metrics capabilities

**Available Tools**:
- `prometheus_query` - Execute instant PromQL queries
- `prometheus_query_range` - Execute range queries over time
- `prometheus_get_metrics` - List all available metrics
- `prometheus_get_labels` - Get all label names
- `prometheus_get_label_values` - Get values for specific labels
- `prometheus_get_targets` - Get service discovery targets
- `prometheus_get_alerts` - Get active alerts
- `prometheus_get_rules` - Get alerting/recording rules
- `prometheus_check_health` - Health check
- `prometheus_get_cpu_usage` - CPU usage metrics
- `prometheus_get_memory_usage` - Memory usage metrics
- `prometheus_get_disk_usage` - Disk usage metrics

**Configuration**:
```bash
PROMETHEUS_URL=http://localhost:9090
PROMETHEUS_AUTH_TOKEN=optional-bearer-token
```

### Neo4j MCP Server (`neo4j_server.py`)

**Port**: 8001  
**Purpose**: Provides graph database query and analysis capabilities

**Available Tools**:
- `neo4j_execute_cypher` - Execute Cypher queries
- `neo4j_get_schema` - Get database schema info
- `neo4j_search_nodes` - Search nodes by label/properties
- `neo4j_find_shortest_path` - Find shortest paths between nodes
- `neo4j_get_node_counts` - Count nodes by label
- `neo4j_get_relationship_counts` - Count relationships by type
- `neo4j_check_connection` - Connection health check

**Configuration**:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

## Usage Examples

### Prometheus Queries

```python
# CPU usage for last hour
{
  "tool": "prometheus_query",
  "arguments": {
    "query": "100 - (avg(rate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)"
  }
}

# Memory usage by instance
{
  "tool": "prometheus_get_memory_usage",
  "arguments": {
    "instance": "localhost:9100"
  }
}
```

### Neo4j Queries

```python
# Get database schema
{
  "tool": "neo4j_get_schema",
  "arguments": {}
}

# Search for Person nodes
{
  "tool": "neo4j_search_nodes", 
  "arguments": {
    "label": "Person",
    "properties": {"name": "John"},
    "limit": 10
  }
}

# Execute custom Cypher
{
  "tool": "neo4j_execute_cypher",
  "arguments": {
    "query": "MATCH (n:Person) RETURN n.name LIMIT 5",
    "read_only": true
  }
}
```

## Integration with Agents

The agents automatically discover and use these MCP servers:

1. **Agent startup** - Agents connect to MCP servers via URLs in configuration
2. **Tool discovery** - Agents fetch available tools from each server
3. **Tool execution** - Agents call tools via MCP protocol
4. **Fallback** - If MCP servers unavailable, agents use direct implementations

## Development

### Adding New Tools

1. **Prometheus**: Add tool definition to `handle_list_tools()` and implementation to `handle_call_tool()`
2. **Neo4j**: Add tool definition to `handle_list_tools()` and implementation to `handle_call_tool()`

### Testing Tools

```bash
# Test tool directly (requires mcp client)
echo '{"tool": "prometheus_check_health", "arguments": {}}' | python3 prometheus_server.py

# Test via agent
cd ../agents
python3 main.py --agent prometheus --query "Check Prometheus health"
```

### Monitoring

- **Logs**: Both servers log to stdout with structured logging
- **Health**: Each server provides health check endpoints
- **Process Management**: Use `start_mcp_servers.py` for production monitoring

## Troubleshooting

### Common Issues

1. **Connection Failed**:
   - Verify Prometheus/Neo4j services are running
   - Check connection credentials and URLs
   - Review server logs for error details

2. **Tool Not Found**:
   - Ensure MCP servers are running on correct ports (8000, 8001)
   - Check agent MCP client configuration
   - Verify tool names match exactly

3. **Permission Denied**:
   - Check Neo4j user permissions for read/write operations
   - Verify Prometheus authentication tokens

4. **MCP Servers Exit in Docker**:
   - Check if processes are running: `docker exec codon-neo4j-mcp pgrep -f "neo4j_server.py"`
   - Restart containers: `docker compose restart neo4j-mcp prometheus-mcp`
   - View logs: `docker compose logs neo4j-mcp prometheus-mcp`

**Note**: MCP servers in Docker run as stdio-based background processes with `sleep infinity` to keep containers alive. They communicate via stdin/stdout using the MCP protocol, not HTTP endpoints.

### Debug Mode

```bash
# Run with debug logging
PYTHONPATH=. python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import prometheus_server
"
```

## Security Considerations

- **Neo4j**: Uses parameterized queries to prevent injection
- **Prometheus**: Supports bearer token authentication
- **Network**: Servers run on localhost by default
- **Read-only**: Neo4j queries default to read-only mode

## Production Deployment

For production deployment:

1. Configure proper authentication tokens
2. Use reverse proxy for HTTPS termination
3. Set up monitoring and alerting for MCP servers
4. Configure log aggregation
5. Use process managers like systemd or supervisor

## License

This MCP server implementation is part of the codon-kg project.