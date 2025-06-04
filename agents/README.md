# LangChain/LangGraph Multi-Agent System

Production-ready, modular LangChain/LangGraph agents for infrastructure management, monitoring, and knowledge graph operations.

## Overview

This system provides three specialized agents:

1. **Prometheus Monitoring Agent**: Queries Prometheus metrics, detects anomalies, and monitors system health
2. **Neo4j Knowledge Graph Agent**: Interacts with Neo4j databases using Cypher queries for graph analysis
3. **Infrastructure Management Agent**: Manages AWS resources and Terraform deployments

## Features

- **Modular Architecture**: Each agent is self-contained with its own tools and configuration
- **Security First**: Built-in security features including command validation and audit logging
- **Error Handling**: Robust retry mechanisms and error recovery
- **Configuration Management**: Flexible configuration via environment variables or YAML files
- **Production Ready**: Structured logging, health checks, and monitoring capabilities

## Installation

1. **Clone and setup**:
```bash
cd /Users/bklynlyphe/projects/codon-kg/agents
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials and endpoints
```

3. **Optional: Use YAML configuration**:
```bash
cp example_config.yaml config.yaml
# Edit config.yaml with your settings
```

## Quick Start

### List Available Agents
```bash
python main.py --list-agents
```

### Health Check
```bash
python main.py --health-check
```

### Run Prometheus Agent
```bash
python main.py --agent prometheus --query "Check CPU usage for the last hour"
```

### Run Neo4j Agent
```bash
python main.py --agent neo4j --query "Show me the database schema"
```

### Run Infrastructure Agent
```bash
python main.py --agent infrastructure --query "List all running EC2 instances"
```

## Agent Capabilities

### Prometheus Agent
- Query Prometheus metrics using PromQL
- Monitor active alerts and system health
- Detect statistical anomalies in metrics
- Provide actionable insights from monitoring data

**Example queries**:
```bash
python main.py --agent prometheus --query "Show CPU usage over the last 24 hours"
python main.py --agent prometheus --query "Are there any active alerts?"
python main.py --agent prometheus --query "Detect anomalies in memory usage"
```

### Neo4j Agent
- Execute read-only and write Cypher queries
- Search nodes by properties and relationships
- Find shortest paths between entities
- Analyze graph schema and structure

**Example queries**:
```bash
python main.py --agent neo4j --query "Find all Person nodes with age > 30"
python main.py --agent neo4j --query "What's the shortest path between Alice and Bob?"
python main.py --agent neo4j --query "Show me all relationship types in the database"
```

### Infrastructure Agent
- Terraform lifecycle management (init, plan, apply, destroy)
- AWS resource monitoring (EC2, S3, CloudFormation)
- Infrastructure validation and planning
- Cost and security recommendations

**Example queries**:
```bash
python main.py --agent infrastructure --query "Initialize Terraform in the current directory"
python main.py --agent infrastructure --query "Show me all S3 buckets"
python main.py --agent infrastructure --query "Plan Terraform changes with variables file"
```

## Configuration

### Environment Variables
Set these in your `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=your-anthropic-api-key

# Neo4j (if using Neo4j agent)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# Prometheus (if using Prometheus agent)
PROMETHEUS_URL=http://localhost:9090

# AWS (if using Infrastructure agent)
AWS_REGION=us-east-1
AWS_PROFILE=your-profile
```

### YAML Configuration
Alternatively, use a YAML configuration file:

```bash
python main.py --config config.yaml --agent prometheus --query "Check system health"
```

## Security Features

- **Command Validation**: Dangerous commands are blocked by security policies
- **Audit Logging**: All agent actions are logged with timestamps and context
- **Input Sanitization**: All inputs are validated and sanitized
- **Least Privilege**: Agents operate with minimal required permissions
- **Secure Defaults**: Read-only operations by default, explicit approval for destructive actions

## Advanced Usage

### Using Context
Pass additional context to agents:

```bash
python main.py --agent neo4j --query "Find related nodes" --context '{"limit": 50, "depth": 3}'
```

### Programmatic Usage

```python
from config.settings import get_config
from prometheus.agent import PrometheusAgent
from prometheus.tools import PrometheusConfig
from shared.base_agent import AgentConfig

# Initialize configuration
config = get_config()

# Create agent
prometheus_config = PrometheusConfig(base_url=config.monitoring.prometheus_url)
agent_config = AgentConfig(name="prometheus_agent", system_prompt="Monitor metrics")
agent = PrometheusAgent(agent_config, prometheus_config)

# Run query
result = agent.run("Show me CPU metrics for the last hour")
print(result)
```

## Development

### Project Structure
```
agents/
├── shared/           # Common utilities and base classes
├── prometheus/       # Prometheus monitoring agent
├── neo4j/           # Neo4j knowledge graph agent
├── infrastructure/  # AWS/Terraform management agent
├── config/          # Configuration management
├── main.py          # CLI entry point
└── requirements.txt # Dependencies
```

### Adding New Agents

1. Create a new directory under `agents/`
2. Implement tools following the pattern in existing agents
3. Create an agent class extending `BaseAgent`
4. Add configuration options to `config/settings.py`
5. Register the agent in `main.py`

### Testing

Each agent includes built-in health checks and validation:

```bash
python main.py --health-check
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify API keys and credentials in `.env`
2. **Connection Timeouts**: Check network connectivity to services
3. **Permission Denied**: Ensure proper AWS/database permissions
4. **Module Import Errors**: Verify all dependencies are installed

### Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py --agent prometheus --query "test query"
```

### Health Monitoring

The system includes comprehensive health checks:
- Database connectivity
- API authentication
- Service availability
- Configuration validation

## License

This project follows security and operational best practices for production deployment.