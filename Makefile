# Makefile for Codon Knowledge Graph System
.PHONY: help start stop restart logs status health clean dev build cli

# Default target
.DEFAULT_GOAL := help

# Variables
DOCKER_COMPOSE = docker-compose
SCRIPTS_DIR = scripts

help: ## Show this help message
	@echo "Codon Knowledge Graph - Docker Management"
	@echo "========================================"
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make start              # Start all services"
	@echo "  make dev                # Start in development mode"
	@echo "  make logs SERVICE=web   # View specific service logs"
	@echo "  make cli AGENT=prometheus QUERY='Check health'"

start: ## Start all services in production mode
	@$(SCRIPTS_DIR)/docker-start.sh start full

start-minimal: ## Start minimal services (no Grafana)
	@$(SCRIPTS_DIR)/docker-start.sh start minimal

dev: ## Start in development mode with hot reload
	@$(SCRIPTS_DIR)/docker-start.sh start dev

stop: ## Stop all services
	@$(SCRIPTS_DIR)/docker-start.sh stop

restart: ## Restart all services
	@$(SCRIPTS_DIR)/docker-start.sh restart

logs: ## View logs (use SERVICE=name for specific service)
	@$(SCRIPTS_DIR)/docker-start.sh logs $(SERVICE)

status: ## Show service status
	@$(SCRIPTS_DIR)/docker-start.sh status

health: ## Run health checks
	@$(SCRIPTS_DIR)/docker-health-check.sh

health-verbose: ## Run detailed health checks
	@$(SCRIPTS_DIR)/docker-health-check.sh --verbose

clean: ## Remove all containers and volumes (WARNING: destroys data)
	@$(SCRIPTS_DIR)/docker-start.sh clean

build: ## Build all Docker images
	@echo "Building Docker images..."
	@$(DOCKER_COMPOSE) build --no-cache

rebuild: ## Rebuild and restart services
	@echo "Rebuilding services..."
	@$(DOCKER_COMPOSE) down
	@$(DOCKER_COMPOSE) build --no-cache
	@$(SCRIPTS_DIR)/docker-start.sh start full

cli: ## Run agent CLI command (use AGENT=name QUERY="your query")
ifndef AGENT
	@echo "Error: AGENT parameter is required"
	@echo "Usage: make cli AGENT=prometheus QUERY='Check health'"
	@echo "Available agents: prometheus, neo4j, infrastructure"
	@exit 1
endif
ifndef QUERY
	@echo "Error: QUERY parameter is required"
	@echo "Usage: make cli AGENT=prometheus QUERY='Check health'"
	@exit 1
endif
	@$(SCRIPTS_DIR)/docker-start.sh cli "$(AGENT)" "$(QUERY)"

setup: ## Initial setup - copy environment file and build images
	@echo "Setting up Codon Knowledge Graph system..."
	@if [ ! -f .env ]; then \
		echo "Copying environment template..."; \
		cp .env.docker .env; \
		echo "Please edit .env file and add your API keys"; \
	else \
		echo ".env file already exists"; \
	fi
	@echo "Building Docker images..."
	@$(DOCKER_COMPOSE) build
	@echo ""
	@echo "Setup complete! Next steps:"
	@echo "1. Edit .env file and add your OpenAI or Anthropic API key"
	@echo "2. Run 'make start' to start the system"

# Development helpers
dev-logs: ## View logs in development mode
	@$(DOCKER_COMPOSE) -f docker-compose.yml -f docker/docker-compose.override.yml logs -f

dev-restart: ## Restart in development mode
	@$(DOCKER_COMPOSE) -f docker-compose.yml -f docker/docker-compose.override.yml restart

# Service-specific commands
neo4j-shell: ## Open Neo4j shell
	@$(DOCKER_COMPOSE) exec neo4j cypher-shell -u neo4j -p password123

prometheus-config: ## Reload Prometheus configuration
	@curl -X POST http://localhost:9090/-/reload

grafana-restart: ## Restart Grafana service
	@$(DOCKER_COMPOSE) restart grafana

# Monitoring shortcuts
monitor: ## Open monitoring dashboards in browser
	@echo "Opening monitoring dashboards..."
	@open http://localhost:5000     # Agent Web Interface
	@open http://localhost:3000     # Grafana
	@open http://localhost:9090     # Prometheus
	@open http://localhost:7474     # Neo4j Browser

# Database operations
neo4j-backup: ## Create Neo4j database backup
	@echo "Creating Neo4j backup..."
	@$(DOCKER_COMPOSE) exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j-$(shell date +%Y%m%d-%H%M%S).dump

neo4j-restore: ## Restore Neo4j database (use BACKUP=filename)
ifndef BACKUP
	@echo "Error: BACKUP parameter is required"
	@echo "Usage: make neo4j-restore BACKUP=neo4j-20231201-120000.dump"
	@exit 1
endif
	@echo "Restoring Neo4j backup: $(BACKUP)"
	@$(DOCKER_COMPOSE) stop neo4j
	@$(DOCKER_COMPOSE) exec neo4j neo4j-admin load --from=/backups/$(BACKUP) --database=neo4j --force
	@$(DOCKER_COMPOSE) start neo4j

# Testing
test-agents: ## Test all agents via CLI
	@echo "Testing Prometheus agent..."
	@$(SCRIPTS_DIR)/docker-start.sh cli prometheus "Check Prometheus health"
	@echo "Testing Neo4j agent..."
	@$(SCRIPTS_DIR)/docker-start.sh cli neo4j "Show database schema"

test-mcp: ## Test MCP server connectivity
	@echo "Testing MCP servers..."
	@curl -f http://localhost:8000/health || echo "Prometheus MCP server not responding"
	@curl -f http://localhost:8001/health || echo "Neo4j MCP server not responding"

# Cleanup helpers
clean-images: ## Remove unused Docker images
	@docker image prune -f

clean-volumes: ## Remove unused Docker volumes
	@docker volume prune -f

clean-all: ## Complete cleanup (containers, images, volumes)
	@$(DOCKER_COMPOSE) down -v --remove-orphans
	@docker system prune -af --volumes

# Documentation
docs: ## Generate documentation
	@echo "Generating documentation..."
	@echo "Documentation available in:"
	@echo "  - README.md (main)"
	@echo "  - agents/README_WEBAPP.md (web interface)"
	@echo "  - mcp_servers/README.md (MCP servers)"
	@echo "  - Docker setup in docker/ directory"

info: ## Show system information
	@echo "Codon Knowledge Graph System Information"
	@echo "======================================="
	@echo "Docker Compose project: $(shell $(DOCKER_COMPOSE) config --services | tr '\n' ' ')"
	@echo "Network: codon-network"
	@echo "Volumes: $(shell $(DOCKER_COMPOSE) config --volumes | tr '\n' ' ')"
	@echo ""
	@echo "Service Ports:"
	@echo "  Web Interface:    5000"
	@echo "  Grafana:          3000"
	@echo "  Prometheus:       9090"
	@echo "  Neo4j HTTP:       7474"
	@echo "  Neo4j Bolt:       7687"
	@echo "  Prometheus MCP:   8000"
	@echo "  Neo4j MCP:        8001"