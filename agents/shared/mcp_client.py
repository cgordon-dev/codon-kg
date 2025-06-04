"""
MCP Client Manager for LangChain/LangGraph Agents

This module provides a centralized MCP client management system for connecting
to external Prometheus and Neo4j MCP servers.
"""

import asyncio
from typing import Dict, Any, List, Optional
import structlog
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = structlog.get_logger(__name__)

class MCPClientManager:
    """Manages MCP client connections and tool retrieval."""
    
    def __init__(self, prometheus_config: Dict[str, Any], neo4j_config: Dict[str, Any]):
        self.prometheus_config = prometheus_config
        self.neo4j_config = neo4j_config
        self._client: Optional[MultiServerMCPClient] = None
        self._tools: Optional[List[Any]] = None
        
    async def initialize(self) -> None:
        """Initialize the MCP client with server configurations."""
        try:
            server_config = {
                "prometheus": {
                    "url": self.prometheus_config["url"],
                    "transport": self.prometheus_config["transport"],
                },
                "neo4j": {
                    "url": self.neo4j_config["url"], 
                    "transport": self.neo4j_config["transport"],
                }
            }
            
            self._client = MultiServerMCPClient(server_config)
            logger.info("MCP client initialized", servers=list(server_config.keys()))
            
        except Exception as e:
            logger.error("Failed to initialize MCP client", error=str(e))
            raise
    
    async def get_tools(self) -> List[Any]:
        """Retrieve all available tools from MCP servers."""
        if not self._client:
            await self.initialize()
            
        try:
            if not self._tools:
                self._tools = await self._client.get_tools()
                logger.info("Retrieved tools from MCP servers", tool_count=len(self._tools))
            
            return self._tools
            
        except Exception as e:
            logger.error("Failed to retrieve MCP tools", error=str(e))
            raise
    
    async def get_prometheus_tools(self) -> List[Any]:
        """Get tools specifically for Prometheus MCP server."""
        all_tools = await self.get_tools()
        prometheus_tools = [tool for tool in all_tools if tool.name.startswith("prometheus")]
        logger.info("Filtered Prometheus tools", tool_count=len(prometheus_tools))
        return prometheus_tools
    
    async def get_neo4j_tools(self) -> List[Any]:
        """Get tools specifically for Neo4j MCP server."""
        all_tools = await self.get_tools()
        neo4j_tools = [tool for tool in all_tools if tool.name.startswith("neo4j")]
        logger.info("Filtered Neo4j tools", tool_count=len(neo4j_tools))
        return neo4j_tools
    
    async def close(self) -> None:
        """Close the MCP client connection."""
        if self._client:
            try:
                await self._client.close()
                logger.info("MCP client closed")
            except Exception as e:
                logger.error("Error closing MCP client", error=str(e))
            finally:
                self._client = None
                self._tools = None

def create_mcp_client(prometheus_config: Dict[str, Any], neo4j_config: Dict[str, Any]) -> MCPClientManager:
    """Factory function to create MCP client manager."""
    return MCPClientManager(prometheus_config, neo4j_config)