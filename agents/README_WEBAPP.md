# Agent Web Interface

A Flask-based web interface for interacting with LangChain/LangGraph agents.

## Features

- **Responsive Web UI**: Bootstrap 5-based interface that works on desktop and mobile
- **Multi-Agent Support**: Interact with Prometheus, Neo4j, and Infrastructure agents
- **Real-time Health Monitoring**: View agent status and health checks
- **REST API**: Programmatic access to agent functionality
- **Example Queries**: Pre-built example queries for each agent type

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Web Interface**:
   ```bash
   python app.py
   ```

3. **Access the Interface**:
   Open http://localhost:5000 in your browser

## Usage

### Web Interface

- **Home Page**: Overview of all agents with quick query form
- **Agent Pages**: Dedicated pages for each agent with examples
- **Health Dashboard**: Real-time status of all agents

### REST API

Execute queries programmatically:

```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "prometheus",
    "query": "Check CPU usage for the last hour",
    "context": {}
  }'
```

### Command Line Options

```bash
python app.py --host 0.0.0.0 --port 8080 --debug
```

- `--host`: Host to bind to (default: 127.0.0.1)
- `--port`: Port to bind to (default: 5000)
- `--debug`: Enable debug mode
- `--config`: Path to configuration file

## API Endpoints

- `GET /` - Main web interface
- `GET /agent/<name>` - Individual agent page
- `POST /api/query` - Execute agent query
- `GET /api/agents` - List all agents
- `GET /api/health` - Health check
- `POST /form/query` - Form-based query submission

## Agent Types

### Prometheus Agent
- Monitor metrics and system health
- Check CPU, memory, disk usage
- View active alerts
- Query Prometheus data

### Neo4j Agent
- Execute Cypher queries
- Explore graph structure
- Find relationships and paths
- Analyze node patterns

### Infrastructure Agent
- Manage AWS resources
- Terraform operations
- CloudFormation monitoring
- EC2 and S3 management

## Development

The web interface integrates with the existing `AgentManager` class from `main.py`, providing a user-friendly way to interact with your LangChain/LangGraph agents during development and testing.

### File Structure

```
agents/
├── app.py              # Flask web application
├── templates/          # HTML templates
│   ├── base.html      # Base template with Bootstrap 5
│   ├── index.html     # Home page
│   ├── agent.html     # Individual agent page
│   └── error.html     # Error pages
└── main.py            # Existing agent manager
```

### Security Notes

- Change the Flask secret key in production
- Consider adding authentication for production deployments
- Review CORS settings if needed for API access
- Ensure proper input validation and sanitization