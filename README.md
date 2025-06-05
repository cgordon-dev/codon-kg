# 🧬 Codon Knowledge Graph

A comprehensive knowledge graph system with intelligent agents for Neo4j database management, Prometheus monitoring, and AWS infrastructure automation.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key (or Anthropic)
- 8GB+ RAM recommended

### 1. Setup Environment
```bash
# Copy and configure environment
cp .env.docker .env

# Edit .env and add your API key
OPENAI_API_KEY=your-openai-api-key-here
```

### 2. Start All Services
```bash
docker compose up -d
```

### 3. Access the System
- **Web Interface**: http://localhost:5000
- **Neo4j Browser**: http://localhost:7474 (neo4j/password123)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Data Layer    │   MCP Servers   │     Agent Layer         │
│                 │                 │                         │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────────────┐ │
│ │   Neo4j     │ │ │ Neo4j MCP   │ │ │   Agent Web UI      │ │
│ │  :7474/7687 │ │ │   :8001     │ │ │       :5000         │ │
│ └─────────────┘ │ └─────────────┘ │ └─────────────────────┘ │
│                 │                 │                         │
│ ┌─────────────┐ │ ┌─────────────┐ │                         │
│ │ Prometheus  │ │ │Prometheus   │ │                         │
│ │    :9090    │ │ │ MCP :8000   │ │                         │
│ └─────────────┘ │ └─────────────┘ │                         │
│                 │                 │                         │
│ ┌─────────────┐ │                 │                         │
│ │  Grafana    │ │                 │                         │
│ │   :3000     │ │                 │                         │
│ └─────────────┘ │                 │                         │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## 🤖 Available Agents

### Neo4j Agent
- Graph database queries and analysis
- Schema exploration and optimization
- Data import/export operations
- Cypher query generation and execution

### Prometheus Agent  
- Metrics collection and analysis
- Alert management
- Performance monitoring
- Custom query execution

### Infrastructure Agent
- AWS resource management
- Terraform operations
- Infrastructure monitoring
- Cost optimization

## 🔧 Service Details

| Service | Port | Purpose | Credentials |
|---------|------|---------|-------------|
| agent-web | 5000 | Main web interface | - |
| neo4j | 7474/7687 | Graph database | neo4j/password123 |
| prometheus | 9090 | Metrics system | - |
| grafana | 3000 | Dashboards | admin/admin123 |
| neo4j-mcp | 8001 | Neo4j MCP server | - |
| prometheus-mcp | 8000 | Prometheus MCP server | - |

## 📚 Documentation

- **[Docker Setup](docs/docker/README.md)** - Complete Docker orchestration guide
- **[Agents](docs/agents/README.md)** - Agent documentation and API reference
- **[MCP Servers](docs/mcp-servers/README.md)** - Model Context Protocol servers
- **[Memory Integration](docs/memory-integration/README.md)** - Memory and persistence
- **[LangSmith Integration](docs/integrations/langsmith.md)** - Tracing and monitoring

## 🛠️ Development

### Local Development
```bash
# Start in development mode
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker compose logs -f agent-web

# Execute commands in container
docker compose exec agent-web python main.py --help
```

### Manual Setup (Without Docker)
```bash
# Install dependencies
pip install -r agents/requirements.txt
pip install -r mcp_servers/requirements.txt

# Start services manually
python agents/app.py
python mcp_servers/neo4j_server.py
python mcp_servers/prometheus_server.py
```

## 🔍 Monitoring & Health

### Health Checks
```bash
# Check all services
docker compose ps

# Check specific service logs
docker compose logs neo4j-mcp
docker compose logs prometheus-mcp

# Verify MCP processes
docker exec codon-neo4j-mcp pgrep -f "neo4j_server.py"
docker exec codon-prometheus-mcp pgrep -f "prometheus_server.py"
```

### Monitoring Stack
- **Prometheus**: Metrics collection from all services
- **Grafana**: Pre-configured dashboards and visualizations  
- **Node Exporter**: System-level metrics
- **Built-in Health Checks**: Container health monitoring

## ⚙️ Configuration

### Environment Variables
```bash
# LLM Configuration (Required)
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4.1-mini

# Database Configuration (Auto-configured)
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# Monitoring Configuration (Auto-configured)
PROMETHEUS_URL=http://prometheus:9090

# Optional: LangSmith Tracing
LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=codon-kg-agents

# Optional: AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

## 🔒 Security

### Production Considerations
- Change default passwords (Neo4j, Grafana)
- Use environment variables for secrets
- Configure firewall rules
- Enable HTTPS with reverse proxy
- Use Docker secrets for sensitive data

### Network Security
- Services communicate via isolated Docker network
- No external access to MCP servers (stdio only)
- Database access restricted to internal network

## 🐛 Troubleshooting

### Common Issues

**Services won't start**:
```bash
docker compose ps -a
docker compose logs [service-name]
```

**MCP servers not running**:
```bash
# Check if processes are running
docker exec codon-neo4j-mcp pgrep -f "neo4j_server.py"
docker exec codon-prometheus-mcp pgrep -f "prometheus_server.py"

# Restart MCP services
docker compose restart neo4j-mcp prometheus-mcp
```

**Database connection issues**:
```bash
# Check Neo4j status
docker compose exec neo4j cypher-shell -u neo4j -p password123 "RETURN 1"

# Check Prometheus
curl http://localhost:9090/-/healthy
```

**API key errors**:
```bash
# Verify API key in environment
docker compose exec agent-web env | grep API_KEY

# Update and restart
docker compose restart agent-web
```

### Clean Reset
```bash
# Complete cleanup
docker compose down -v
docker system prune -f

# Fresh start
docker compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test locally
4. Commit changes: `git commit -m "Add feature"`
5. Push to branch: `git push origin feature-name`
6. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Projects

- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/python-sdk)
- [Neo4j](https://neo4j.com/)
- [Prometheus](https://prometheus.io/)
- [LangChain](https://langchain.com/)

---

**Ready to explore your data with intelligent agents?** 🚀

Start with: `docker compose up -d` and visit http://localhost:5000
