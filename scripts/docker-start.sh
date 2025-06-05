#!/bin/bash
# Docker Start Script for Codon Knowledge Graph System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1 && ! docker compose version > /dev/null 2>&1; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Check environment file
check_environment() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.docker" ]; then
            print_warning ".env not found, copying from .env.docker"
            cp .env.docker .env
            print_warning "Please edit .env file and add your API keys before continuing"
            read -p "Press Enter to continue after updating .env file..."
        else
            print_error ".env file not found. Please create one with your configuration."
            exit 1
        fi
    fi
    
    # Check for required API key
    if ! grep -q "^OPENAI_API_KEY=.*[^=]" .env && ! grep -q "^ANTHROPIC_API_KEY=.*[^=]" .env; then
        print_warning "No API keys found in .env file. Please add your OpenAI or Anthropic API key."
        read -p "Press Enter to continue anyway (some features may not work)..."
    fi
    
    print_success "Environment configuration checked"
}

# Function to start services
start_services() {
    local mode=$1
    
    print_status "Starting Codon Knowledge Graph system in $mode mode..."
    
    case $mode in
        "full")
            print_status "Starting all services including Grafana..."
            docker-compose up -d
            ;;
        "minimal")
            print_status "Starting minimal services (no Grafana)..."
            docker-compose up -d neo4j prometheus node-exporter neo4j-mcp prometheus-mcp agent-web
            ;;
        "dev")
            print_status "Starting in development mode with hot reload..."
            docker-compose -f docker-compose.yml -f docker/docker-compose.override.yml up -d
            ;;
        *)
            print_error "Unknown mode: $mode"
            print_status "Available modes: full, minimal, dev"
            exit 1
            ;;
    esac
}

# Function to wait for services
wait_for_services() {
    print_status "Waiting for services to become healthy..."
    
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps | grep -q "Up (healthy)"; then
            local healthy_count=$(docker-compose ps | grep -c "Up (healthy)" || echo "0")
            local total_count=$(docker-compose ps | grep -c "Up" || echo "0")
            
            if [ "$healthy_count" -gt 0 ]; then
                print_status "Services health check: $healthy_count/$total_count healthy"
                
                # Check if web interface is ready
                if curl -sf http://localhost:5000/api/health > /dev/null 2>&1; then
                    print_success "Web interface is ready!"
                    break
                fi
            fi
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 5
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_warning "Services are taking longer than expected to start"
        print_status "You can check service status with: docker-compose ps"
    fi
}

# Function to show service URLs
show_urls() {
    print_success "Codon Knowledge Graph system is running!"
    echo ""
    echo "📊 Service URLs:"
    echo "  🌐 Agent Web Interface:  http://localhost:5000"
    echo "  📈 Grafana Dashboard:    http://localhost:3000 (admin/admin123)"
    echo "  🔍 Prometheus:           http://localhost:9090"
    echo "  🗄️  Neo4j Browser:        http://localhost:7474 (neo4j/password123)"
    echo ""
    echo "🔧 MCP Servers:"
    echo "  📊 Prometheus MCP:       http://localhost:8000"
    echo "  🗄️  Neo4j MCP:           http://localhost:8001"
    echo ""
    echo "🚀 Quick Commands:"
    echo "  View logs:               docker-compose logs -f"
    echo "  Stop services:           docker-compose down"
    echo "  Restart services:        docker-compose restart"
    echo "  View service status:     docker-compose ps"
    echo ""
}

# Function to run CLI commands
run_cli() {
    local agent=$1
    local query=$2
    
    if [ -z "$agent" ] || [ -z "$query" ]; then
        print_error "Usage: $0 cli <agent> <query>"
        print_status "Available agents: prometheus, neo4j, infrastructure"
        exit 1
    fi
    
    print_status "Running CLI command: $agent -> $query"
    docker-compose exec agent-cli python main.py --agent "$agent" --query "$query"
}

# Main script logic
main() {
    local command=${1:-"start"}
    local mode=${2:-"full"}
    
    case $command in
        "start")
            check_docker
            check_docker_compose
            check_environment
            start_services "$mode"
            wait_for_services
            show_urls
            ;;
        "stop")
            print_status "Stopping Codon Knowledge Graph system..."
            docker-compose down
            print_success "System stopped"
            ;;
        "restart")
            print_status "Restarting Codon Knowledge Graph system..."
            docker-compose restart
            wait_for_services
            show_urls
            ;;
        "logs")
            docker-compose logs -f ${2:-""}
            ;;
        "status")
            docker-compose ps
            ;;
        "cli")
            run_cli "$2" "$3"
            ;;
        "clean")
            print_warning "This will remove all containers and volumes. Data will be lost!"
            read -p "Are you sure? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker-compose down -v --remove-orphans
                docker system prune -f
                print_success "System cleaned"
            else
                print_status "Clean cancelled"
            fi
            ;;
        "help"|"-h"|"--help")
            echo "Codon Knowledge Graph Docker Management Script"
            echo ""
            echo "Usage: $0 [command] [options]"
            echo ""
            echo "Commands:"
            echo "  start [mode]     Start the system (modes: full, minimal, dev)"
            echo "  stop             Stop all services"
            echo "  restart          Restart all services"
            echo "  logs [service]   View logs (optionally for specific service)"
            echo "  status           Show service status"
            echo "  cli <agent> <query>  Run agent CLI command"
            echo "  clean            Remove all containers and volumes"
            echo "  help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 start full                    # Start all services"
            echo "  $0 start minimal                 # Start without Grafana"
            echo "  $0 start dev                     # Start in development mode"
            echo "  $0 logs agent-web                # View web interface logs"
            echo "  $0 cli prometheus 'Check health' # Run Prometheus agent"
            ;;
        *)
            print_error "Unknown command: $command"
            print_status "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"