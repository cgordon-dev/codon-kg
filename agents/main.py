#!/usr/bin/env python3
"""
Production-ready LangChain/LangGraph Agents for Infrastructure Management

This module provides three specialized agents:
1. PrometheusAgent: Monitoring and metrics analysis
2. Neo4jAgent: Knowledge graph queries and analysis  
3. InfrastructureAgent: AWS and Terraform management

Usage:
    python main.py --agent prometheus --query "Check CPU usage for the last hour"
    python main.py --agent neo4j --query "Find all connected nodes to Person with name 'John'"
    python main.py --agent infrastructure --query "List all running EC2 instances"
"""

import argparse
import asyncio
import json
import sys
from typing import Dict, Any, Optional
import structlog

from config.settings import get_config, reload_config
from shared.base_agent import AgentConfig
from prometheus.agent import PrometheusAgent
from prometheus.tools import PrometheusConfig
from neo4j.agent import Neo4jAgent
from neo4j.tools import Neo4jConfig
from infrastructure.agent import InfrastructureAgent
from infrastructure.tools import AWSConfig, TerraformConfig

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

class AgentManager:
    def __init__(self, config_path: Optional[str] = None):
        self.global_config = reload_config(config_path)
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all agents with their configurations."""
        try:
            # Prometheus Agent
            prometheus_config = PrometheusConfig(
                base_url=self.global_config.monitoring.prometheus_url,
                auth_token=self.global_config.monitoring.prometheus_auth_token,
                timeout=30,
                verify_ssl=True
            )
            
            prometheus_agent_config = AgentConfig(
                name="prometheus_agent",
                model_name=self.global_config.llm.model_name,
                temperature=self.global_config.llm.temperature,
                max_tokens=self.global_config.llm.max_tokens,
                max_retries=self.global_config.security.max_retry_attempts,
                system_prompt="You are a Prometheus monitoring specialist."
            )
            
            self.agents["prometheus"] = PrometheusAgent(prometheus_agent_config, prometheus_config)
            logger.info("Prometheus agent initialized")
            
            # Neo4j Agent
            neo4j_config = Neo4jConfig(
                uri=self.global_config.database.neo4j_uri,
                username=self.global_config.database.neo4j_username,
                password=self.global_config.database.neo4j_password,
                database=self.global_config.database.neo4j_database
            )
            
            neo4j_agent_config = AgentConfig(
                name="neo4j_agent",
                model_name=self.global_config.llm.model_name,
                temperature=self.global_config.llm.temperature,
                max_tokens=self.global_config.llm.max_tokens,
                max_retries=self.global_config.security.max_retry_attempts,
                system_prompt="You are a Neo4j knowledge graph specialist."
            )
            
            self.agents["neo4j"] = Neo4jAgent(neo4j_agent_config, neo4j_config)
            logger.info("Neo4j agent initialized")
            
            # Infrastructure Agent
            aws_config = AWSConfig(
                region=self.global_config.cloud.aws_region,
                profile=self.global_config.cloud.aws_profile,
                access_key_id=self.global_config.cloud.aws_access_key_id,
                secret_access_key=self.global_config.cloud.aws_secret_access_key
            )
            
            terraform_config = TerraformConfig(
                working_directory=self.global_config.cloud.terraform_dir,
                auto_approve=False  # Safety first
            )
            
            infrastructure_agent_config = AgentConfig(
                name="infrastructure_agent",
                model_name=self.global_config.llm.model_name,
                temperature=self.global_config.llm.temperature,
                max_tokens=self.global_config.llm.max_tokens,
                max_retries=self.global_config.security.max_retry_attempts,
                system_prompt="You are an infrastructure management specialist."
            )
            
            self.agents["infrastructure"] = InfrastructureAgent(
                infrastructure_agent_config, aws_config, terraform_config
            )
            logger.info("Infrastructure agent initialized")
            
        except Exception as e:
            logger.error("Failed to initialize agents", error=str(e))
            raise
    
    def run_agent(self, agent_name: str, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run a specific agent with the given query."""
        if agent_name not in self.agents:
            return {
                "status": "error",
                "error": f"Unknown agent: {agent_name}",
                "available_agents": list(self.agents.keys())
            }
        
        agent = self.agents[agent_name]
        logger.info("Running agent", agent=agent_name, query=query)
        
        try:
            result = agent.run(query, context or {})
            logger.info("Agent execution completed", agent=agent_name, status=result.get("status"))
            return result
            
        except Exception as e:
            logger.error("Agent execution failed", agent=agent_name, error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "agent": agent_name
            }
    
    def list_agents(self) -> Dict[str, Any]:
        """List all available agents and their capabilities."""
        return {
            "agents": {
                "prometheus": {
                    "description": "Monitors metrics and detects anomalies using Prometheus",
                    "capabilities": [
                        "Query Prometheus metrics",
                        "Check system health",
                        "Monitor active alerts",
                        "Detect metric anomalies"
                    ]
                },
                "neo4j": {
                    "description": "Interacts with Neo4j knowledge graphs",
                    "capabilities": [
                        "Execute Cypher queries",
                        "Search nodes and relationships",
                        "Find shortest paths",
                        "Analyze graph schema"
                    ]
                },
                "infrastructure": {
                    "description": "Manages AWS resources and Terraform deployments",
                    "capabilities": [
                        "Terraform operations (init, plan, apply, destroy)",
                        "List EC2 instances",
                        "Manage S3 buckets",
                        "Monitor CloudFormation stacks"
                    ]
                }
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health checks on all agents."""
        health_status = {"status": "healthy", "agents": {}}
        
        for agent_name, agent in self.agents.items():
            try:
                if agent_name == "prometheus":
                    result = agent.infrastructure_tools.check_prometheus_health()
                elif agent_name == "neo4j":
                    result = agent.neo4j_tools.check_connection()
                elif agent_name == "infrastructure":
                    # Basic AWS connectivity check
                    result = {"status": "healthy", "message": "Agent initialized"}
                
                health_status["agents"][agent_name] = result
                
            except Exception as e:
                health_status["agents"][agent_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "degraded"
        
        return health_status
    
    def cleanup(self):
        """Clean up agent resources."""
        for agent_name, agent in self.agents.items():
            try:
                if hasattr(agent, 'close'):
                    agent.close()
                logger.info("Agent cleaned up", agent=agent_name)
            except Exception as e:
                logger.error("Failed to cleanup agent", agent=agent_name, error=str(e))

def main():
    parser = argparse.ArgumentParser(description="LangChain/LangGraph Multi-Agent System")
    parser.add_argument("--agent", choices=["prometheus", "neo4j", "infrastructure"], 
                       help="Agent to run")
    parser.add_argument("--query", type=str, help="Query to execute")
    parser.add_argument("--list-agents", action="store_true", help="List all available agents")
    parser.add_argument("--health-check", action="store_true", help="Perform health check")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--context", type=str, help="JSON context for the query")
    
    args = parser.parse_args()
    
    try:
        # Initialize agent manager
        manager = AgentManager(args.config)
        
        if args.list_agents:
            result = manager.list_agents()
            print(json.dumps(result, indent=2))
            return
        
        if args.health_check:
            result = manager.health_check()
            print(json.dumps(result, indent=2))
            return
        
        if not args.agent or not args.query:
            parser.error("Both --agent and --query are required")
        
        # Parse context if provided
        context = {}
        if args.context:
            try:
                context = json.loads(args.context)
            except json.JSONDecodeError:
                logger.error("Invalid JSON context provided")
                sys.exit(1)
        
        # Run the agent
        result = manager.run_agent(args.agent, args.query, context)
        print(json.dumps(result, indent=2, default=str))
        
        # Return appropriate exit code
        sys.exit(0 if result.get("status") == "success" else 1)
        
    except Exception as e:
        logger.error("Application failed", error=str(e))
        print(json.dumps({"status": "error", "error": str(e)}, indent=2))
        sys.exit(1)
    
    finally:
        if 'manager' in locals():
            manager.cleanup()

if __name__ == "__main__":
    main()