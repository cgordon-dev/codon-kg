#!/usr/bin/env python3
"""
Prometheus MCP Server

Provides Prometheus monitoring tools via Model Context Protocol (MCP).
Runs on port 8000 and exposes Prometheus querying capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
from urllib.parse import urljoin

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prometheus-mcp-server")

class PrometheusClient:
    """Client for interacting with Prometheus API."""
    
    def __init__(self, base_url: str = "http://localhost:9090", auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = requests.Session()
        
        if auth_token:
            self.session.headers.update({"Authorization": f"Bearer {auth_token}"})
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to Prometheus API."""
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Prometheus API request failed: {e}")
            raise Exception(f"Prometheus API error: {str(e)}")
    
    def query(self, query: str, time: Optional[str] = None) -> Dict[str, Any]:
        """Execute instant query."""
        params = {"query": query}
        if time:
            params["time"] = time
        
        return self._make_request("/api/v1/query", params)
    
    def query_range(self, query: str, start: str, end: str, step: str = "15s") -> Dict[str, Any]:
        """Execute range query."""
        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step
        }
        
        return self._make_request("/api/v1/query_range", params)
    
    def get_labels(self) -> Dict[str, Any]:
        """Get all label names."""
        return self._make_request("/api/v1/labels")
    
    def get_label_values(self, label: str) -> Dict[str, Any]:
        """Get values for a specific label."""
        return self._make_request(f"/api/v1/label/{label}/values")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metric names."""
        return self._make_request("/api/v1/label/__name__/values")
    
    def get_targets(self) -> Dict[str, Any]:
        """Get service discovery targets."""
        return self._make_request("/api/v1/targets")
    
    def get_alerts(self) -> Dict[str, Any]:
        """Get active alerts."""
        return self._make_request("/api/v1/alerts")
    
    def get_rules(self) -> Dict[str, Any]:
        """Get alerting and recording rules."""
        return self._make_request("/api/v1/rules")
    
    def check_health(self) -> Dict[str, Any]:
        """Check Prometheus health."""
        try:
            return self._make_request("/-/healthy")
        except Exception:
            return self._make_request("/api/v1/query", {"query": "up"})

# Initialize Prometheus client
prometheus_client = PrometheusClient()

# Create MCP server
server = Server("prometheus-mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Prometheus tools."""
    return [
        types.Tool(
            name="prometheus_query",
            description="Execute instant Prometheus query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "PromQL query to execute"
                    },
                    "time": {
                        "type": "string",
                        "description": "Optional timestamp (RFC3339 or Unix timestamp)"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="prometheus_query_range",
            description="Execute range Prometheus query over time period",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "PromQL query to execute"
                    },
                    "start": {
                        "type": "string",
                        "description": "Start time (RFC3339 or Unix timestamp)"
                    },
                    "end": {
                        "type": "string",
                        "description": "End time (RFC3339 or Unix timestamp)"
                    },
                    "step": {
                        "type": "string",
                        "description": "Query resolution step width (e.g., '15s', '1m')",
                        "default": "15s"
                    }
                },
                "required": ["query", "start", "end"]
            }
        ),
        types.Tool(
            name="prometheus_get_metrics",
            description="Get list of all available metrics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="prometheus_get_labels",
            description="Get all label names",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="prometheus_get_label_values",
            description="Get values for a specific label",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Label name to get values for"
                    }
                },
                "required": ["label"]
            }
        ),
        types.Tool(
            name="prometheus_get_targets",
            description="Get service discovery targets and their status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="prometheus_get_alerts",
            description="Get currently active alerts",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="prometheus_get_rules",
            description="Get alerting and recording rules",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="prometheus_check_health",
            description="Check Prometheus server health status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="prometheus_get_cpu_usage",
            description="Get CPU usage metrics for the last hour",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {
                        "type": "string",
                        "description": "Optional instance filter"
                    }
                }
            }
        ),
        types.Tool(
            name="prometheus_get_memory_usage",
            description="Get memory usage metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {
                        "type": "string",
                        "description": "Optional instance filter"
                    }
                }
            }
        ),
        types.Tool(
            name="prometheus_get_disk_usage",
            description="Get disk usage metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {
                        "type": "string",
                        "description": "Optional instance filter"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    try:
        if name == "prometheus_query":
            result = prometheus_client.query(
                query=arguments["query"],
                time=arguments.get("time")
            )
            
        elif name == "prometheus_query_range":
            result = prometheus_client.query_range(
                query=arguments["query"],
                start=arguments["start"],
                end=arguments["end"],
                step=arguments.get("step", "15s")
            )
            
        elif name == "prometheus_get_metrics":
            result = prometheus_client.get_metrics()
            
        elif name == "prometheus_get_labels":
            result = prometheus_client.get_labels()
            
        elif name == "prometheus_get_label_values":
            result = prometheus_client.get_label_values(arguments["label"])
            
        elif name == "prometheus_get_targets":
            result = prometheus_client.get_targets()
            
        elif name == "prometheus_get_alerts":
            result = prometheus_client.get_alerts()
            
        elif name == "prometheus_get_rules":
            result = prometheus_client.get_rules()
            
        elif name == "prometheus_check_health":
            result = prometheus_client.check_health()
            
        elif name == "prometheus_get_cpu_usage":
            instance_filter = f'{{instance="{arguments["instance"]}"}}' if arguments.get("instance") else ""
            query = f"100 - (avg(rate(node_cpu_seconds_total{{mode='idle'{instance_filter}}}[5m])) * 100)"
            result = prometheus_client.query(query)
            
        elif name == "prometheus_get_memory_usage":
            instance_filter = f'{{instance="{arguments["instance"]}"}}' if arguments.get("instance") else ""
            query = f"(1 - (node_memory_MemAvailable_bytes{instance_filter} / node_memory_MemTotal_bytes{instance_filter})) * 100"
            result = prometheus_client.query(query)
            
        elif name == "prometheus_get_disk_usage":
            instance_filter = f'{{instance="{arguments["instance"]}"}}' if arguments.get("instance") else ""
            query = f"100 - ((node_filesystem_avail_bytes{{fstype!='tmpfs'{instance_filter}}} / node_filesystem_size_bytes{{fstype!='tmpfs'{instance_filter}}}) * 100)"
            result = prometheus_client.query(query)
            
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [types.TextContent(
            type="text", 
            text=json.dumps({
                "status": "error",
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the Prometheus MCP server."""
    # Update Prometheus client configuration from environment
    import os
    prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    prometheus_token = os.getenv("PROMETHEUS_AUTH_TOKEN")
    
    global prometheus_client
    prometheus_client = PrometheusClient(prometheus_url, prometheus_token)
    
    logger.info(f"Starting Prometheus MCP server on http://localhost:8000")
    logger.info(f"Connecting to Prometheus at: {prometheus_url}")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            NotificationOptions()
        )

if __name__ == "__main__":
    asyncio.run(main())