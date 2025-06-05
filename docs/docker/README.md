# 🐳 Docker Orchestration for Codon Knowledge Graph

The **easiest way** to run the entire Codon Knowledge Graph system with all services orchestrated via Docker Compose.

## 🚀 Quick Start

### 1. **One-Command Setup**
```bash
make setup
```

### 2. **Add Your API Key**
Edit `.env` file and add your OpenAI API key:
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

### 3. **Start Everything**
```bash
make start
```

### 4. **Access the System**
- 🌐 **Agent Web Interface**: http://localhost:5000
- 📈 **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- 🔍 **Prometheus**: http://localhost:9090
- 🗄️ **Neo4j Browser**: http://localhost:7474 (neo4j/password123)

## 📋 Available Commands

### **Basic Operations**
```bash
make start          # Start all services
make stop           # Stop all services  
make restart        # Restart all services
make status         # Show service status
make health         # Run health checks
make logs           # View all logs
```

### **Development Mode**
```bash
make dev            # Start with hot reload
make dev-logs       # View development logs
```

### **Agent Commands**
```bash
# Run agent queries via CLI
make cli AGENT=prometheus QUERY="Check CPU usage"
make cli AGENT=neo4j QUERY="Show database schema"
make cli AGENT=infrastructure QUERY="List EC2 instances"
```

### **Service Management**
```bash
make start-minimal  # Start without Grafana
make clean          # Remove all containers/volumes
make rebuild        # Rebuild and restart
```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                   │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Data Layer    │   MCP Servers   │     Agent Layer         │
│                 │                 │                         │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────────────┐ │
│ │   Neo4j     │ │ │ Neo4j MCP   │ │ │   Agent Web UI      │ │
│ │  :7474/7687 │ │ │   :8001     │ │ │       :5000         │ │
│ └─────────────┘ │ └─────────────┘ │ └─────────────────────┘ │
│                 │                 │                         │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────────────┐ │
│ │ Prometheus  │ │ │Prometheus   │ │ │   Agent CLI         │ │
│ │    :9090    │ │ │ MCP :8000   │ │ │   (on demand)       │ │
│ └─────────────┘ │ └─────────────┘ │ └─────────────────────┘ │
│                 │                 │                         │
│ ┌─────────────┐ │                 │                         │
│ │  Grafana    │ │                 │                         │
│ │   :3000     │ │                 │                         │
│ └─────────────┘ │                 │                         │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## 🔧 Service Details

### **Core Services**
| Service | Port | Purpose |
|---------|------|---------|
| agent-web | 5000 | Main web interface for interacting with agents |
| neo4j | 7474/7687 | Graph database for knowledge storage |
| prometheus | 9090 | Metrics and monitoring system |
| neo4j-mcp | 8001 | MCP server for Neo4j tools |
| prometheus-mcp | 8000 | MCP server for Prometheus tools |

### **Optional Services**
| Service | Port | Purpose |
|---------|------|---------|
| grafana | 3000 | Visualization dashboards |
| node-exporter | 9100 | System metrics collection |
| agent-cli | - | CLI interface (on-demand) |

## 📊 Service URLs & Credentials

### **Web Interfaces**
- **Agent Interface**: http://localhost:5000
- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin123`
- **Prometheus**: http://localhost:9090
- **Neo4j Browser**: http://localhost:7474
  - Username: `neo4j`
  - Password: `password123`

### **API Endpoints**
- **Agent API**: http://localhost:5000/api/
- **Prometheus MCP**: Port 8000 (stdio interface, not HTTP)
- **Neo4j MCP**: Port 8001 (stdio interface, not HTTP)

## 🎛️ Configuration

### **Environment Variables**
All configuration is done via `.env` file:

```bash
# Required: Choose your LLM provider
LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here

# Auto-configured for Docker
NEO4J_URI=bolt://neo4j:7687
PROMETHEUS_URL=http://prometheus:9090

# Optional: AWS credentials for infrastructure agent
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

### **Development Mode**
Development mode provides:
- Hot reload for code changes
- Volume mounts for live editing
- Debug logging
- Direct file access

```bash
make dev  # Start in development mode
```

## 🔍 Monitoring & Health Checks

### **Built-in Health Checks**
```bash
make health          # Quick health check
make health-verbose  # Detailed health check
```

### **Manual Checks**
```bash
# Check service status
make status

# View logs
make logs                    # All services
make logs SERVICE=agent-web  # Specific service

# Test agents
make test-agents

# Test MCP connectivity  
make test-mcp
```

### **Monitoring Stack**
- **Prometheus**: Collects metrics from all services
- **Grafana**: Visualizes metrics with dashboards
- **Node Exporter**: Provides system-level metrics
- **Built-in Health Checks**: HTTP endpoints for service status

## 🛠️ Development Workflow

### **Code Changes**
1. **Development Mode**: `make dev`
2. **Edit Code**: Changes automatically reload
3. **View Logs**: `make dev-logs`
4. **Test Changes**: `make test-agents`

### **Database Operations**
```bash
# Access Neo4j shell
make neo4j-shell

# Backup database
make neo4j-backup

# Restore database
make neo4j-restore BACKUP=filename.dump
```

### **Service Management**
```bash
# Restart specific services
docker-compose restart agent-web

# View specific logs
docker-compose logs -f prometheus-mcp

# Execute commands in containers
docker-compose exec agent-web python main.py --help
```

## 🔒 Security Considerations

### **Production Deployment**
- **Change Default Passwords**: Update Neo4j and Grafana passwords
- **API Keys**: Use environment variables, never commit keys
- **Network**: Configure firewall rules for production
- **HTTPS**: Use reverse proxy for SSL termination
- **Secrets**: Use Docker secrets or external secret management

### **Development Safety**
- **Data Isolation**: Each environment uses separate Docker volumes
- **Network Isolation**: Services communicate via Docker network
- **Resource Limits**: Configure memory/CPU limits for production

## 🔧 Troubleshooting

### **Common Issues**

**Services won't start**:
```bash
make health-verbose  # Detailed diagnostics
make logs           # Check error messages
```

**API key errors**:
```bash
# Check .env file
cat .env | grep API_KEY

# Update key and restart
make restart
```

**Database connection issues**:
```bash
# Check Neo4j status
make neo4j-shell

# Restart Neo4j
docker-compose restart neo4j
```

**MCP server issues**:
```bash
# Check MCP server logs
make logs SERVICE=neo4j-mcp
make logs SERVICE=prometheus-mcp

# Test MCP connectivity
make test-mcp

# Verify MCP processes are running
docker exec codon-neo4j-mcp pgrep -f "neo4j_server.py"
docker exec codon-prometheus-mcp pgrep -f "prometheus_server.py"
```

**Note**: MCP servers run as stdio-based services in background processes. They connect to their respective databases but use stdin/stdout for MCP protocol communication, not HTTP endpoints.

### **Debug Commands**
```bash
# Container inspection
docker-compose ps
docker-compose top

# Network debugging
docker network ls
docker network inspect codon-kg_codon-network

# Volume inspection
docker volume ls
docker-compose config --volumes
```

### **Clean Restart**
```bash
# Complete cleanup and fresh start
make clean
make rebuild
```

## 📚 Additional Resources

- **Agent Documentation**: `agents/README_WEBAPP.md`
- **MCP Servers**: `mcp_servers/README.md` 
- **API Reference**: Visit http://localhost:5000/api/ when running
- **Grafana Dashboards**: Pre-configured at http://localhost:3000

## 🎯 Production Deployment

For production deployment:

1. **Configure Environment**:
   ```bash
   cp .env.docker .env.production
   # Edit production values
   ```

2. **Use Production Compose**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. **Set Resource Limits**:
   ```yaml
   services:
     agent-web:
       deploy:
         resources:
           limits:
             memory: 1G
             cpus: '0.5'
   ```

4. **Configure Monitoring**:
   - Set up external monitoring
   - Configure log aggregation
   - Set up alerting rules

The Docker orchestration provides the **easiest** and most reliable way to run the entire Codon Knowledge Graph system! 🚀