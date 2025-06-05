#!/bin/bash
# Health Check Script for Docker Services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    print_status "Checking $service_name..."
    
    if curl -sf -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        print_success "$service_name is healthy"
        return 0
    else
        print_error "$service_name is not responding correctly"
        return 1
    fi
}

# Function to check Docker service status
check_docker_service() {
    local service_name=$1
    local container_name=$2
    
    if docker-compose ps "$service_name" | grep -q "Up (healthy)"; then
        print_success "$container_name is running and healthy"
        return 0
    elif docker-compose ps "$service_name" | grep -q "Up"; then
        print_warning "$container_name is running but not healthy"
        return 1
    else
        print_error "$container_name is not running"
        return 1
    fi
}

# Function to check Neo4j connection
check_neo4j() {
    print_status "Checking Neo4j database connection..."
    
    if docker-compose exec -T neo4j cypher-shell -u neo4j -p password123 "RETURN 'connected' as status" > /dev/null 2>&1; then
        print_success "Neo4j database is accessible"
        return 0
    else
        print_error "Neo4j database connection failed"
        return 1
    fi
}

# Function to check MCP server tools
check_mcp_tools() {
    local server_name=$1
    local port=$2
    
    print_status "Checking $server_name MCP tools..."
    
    # This would need MCP client to properly test
    # For now, just check if the service is responding
    if curl -sf "http://localhost:$port/health" > /dev/null 2>&1; then
        print_success "$server_name MCP server is responding"
        return 0
    else
        print_warning "$server_name MCP server health check not available"
        return 1
    fi
}

# Function to test agent functionality
test_agents() {
    print_status "Testing agent functionality..."
    
    # Test health endpoint
    if curl -sf "http://localhost:5000/api/health" > /dev/null 2>&1; then
        print_success "Agent web interface health check passed"
    else
        print_error "Agent web interface health check failed"
        return 1
    fi
    
    # Test agents list endpoint
    if curl -sf "http://localhost:5000/api/agents" > /dev/null 2>&1; then
        print_success "Agent list endpoint is working"
    else
        print_error "Agent list endpoint failed"
        return 1
    fi
    
    return 0
}

# Main health check routine
main() {
    local detailed=${1:-false}
    
    echo "🏥 Codon Knowledge Graph - Health Check"
    echo "========================================"
    echo ""
    
    local all_healthy=true
    
    # Check Docker services
    print_status "Checking Docker services..."
    echo ""
    
    check_docker_service "neo4j" "Neo4j Database" || all_healthy=false
    check_docker_service "prometheus" "Prometheus" || all_healthy=false
    check_docker_service "node-exporter" "Node Exporter" || all_healthy=false
    check_docker_service "neo4j-mcp" "Neo4j MCP Server" || all_healthy=false
    check_docker_service "prometheus-mcp" "Prometheus MCP Server" || all_healthy=false
    check_docker_service "agent-web" "Agent Web Interface" || all_healthy=false
    
    # Check if Grafana is running (optional service)
    if docker-compose ps grafana | grep -q "Up"; then
        check_docker_service "grafana" "Grafana Dashboard" || all_healthy=false
    else
        print_warning "Grafana is not running (this is optional)"
    fi
    
    echo ""
    
    # Check service endpoints
    print_status "Checking service endpoints..."
    echo ""
    
    check_service "Neo4j HTTP" "http://localhost:7474" || all_healthy=false
    check_service "Prometheus" "http://localhost:9090/-/healthy" || all_healthy=false
    check_service "Agent Web Interface" "http://localhost:5000/api/health" || all_healthy=false
    
    # Check Grafana if running
    if docker-compose ps grafana | grep -q "Up"; then
        check_service "Grafana" "http://localhost:3000/api/health" || all_healthy=false
    fi
    
    echo ""
    
    # Detailed checks
    if [ "$detailed" = "true" ] || [ "$detailed" = "-v" ] || [ "$detailed" = "--verbose" ]; then
        print_status "Running detailed checks..."
        echo ""
        
        check_neo4j || all_healthy=false
        test_agents || all_healthy=false
        
        # Check MCP servers (these might not have health endpoints)
        check_mcp_tools "Prometheus" "8000" || true  # Don't fail on this
        check_mcp_tools "Neo4j" "8001" || true       # Don't fail on this
        
        echo ""
    fi
    
    # Summary
    echo "========================================"
    if [ "$all_healthy" = true ]; then
        print_success "All critical services are healthy! 🎉"
        echo ""
        echo "🌐 Web Interface: http://localhost:5000"
        echo "📊 Prometheus:    http://localhost:9090"
        echo "🗄️  Neo4j:        http://localhost:7474"
        if docker-compose ps grafana | grep -q "Up"; then
            echo "📈 Grafana:       http://localhost:3000"
        fi
        exit 0
    else
        print_error "Some services are not healthy"
        echo ""
        echo "🔍 Troubleshooting:"
        echo "  - Check logs: docker-compose logs [service-name]"
        echo "  - Restart services: docker-compose restart"
        echo "  - Check service status: docker-compose ps"
        exit 1
    fi
}

# Run health check
main "$@"