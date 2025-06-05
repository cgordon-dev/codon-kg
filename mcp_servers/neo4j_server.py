#!/usr/bin/env python3
"""
Neo4j MCP Server

Provides Neo4j graph database tools via Model Context Protocol (MCP).
Runs on port 8001 and exposes Neo4j querying and schema capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
import os

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import Neo4jError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neo4j-mcp-server")

class Neo4jClient:
    """Client for interacting with Neo4j database."""
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=basic_auth(self.username, self.password)
            )
            # Test connection
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def execute_cypher(self, query: str, parameters: Dict[str, Any] = None, read_only: bool = True) -> Dict[str, Any]:
        """Execute a Cypher query."""
        if not self.driver:
            raise Exception("Neo4j driver not connected")
        
        try:
            with self.driver.session(database=self.database) as session:
                if read_only:
                    result = session.run(query, parameters or {})
                else:
                    result = session.write_transaction(lambda tx: tx.run(query, parameters or {}))
                
                records = []
                for record in result:
                    # Convert Neo4j record to dictionary
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # Handle Neo4j types
                        if hasattr(value, '_properties'):  # Node or Relationship
                            record_dict[key] = dict(value._properties)
                            if hasattr(value, 'labels'):  # Node
                                record_dict[key]['_labels'] = list(value.labels)
                            if hasattr(value, 'type'):  # Relationship
                                record_dict[key]['_type'] = value.type
                        else:
                            record_dict[key] = value
                    records.append(record_dict)
                
                return {
                    "status": "success",
                    "records": records,
                    "count": len(records),
                    "query": query,
                    "parameters": parameters or {}
                }
                
        except Neo4jError as e:
            logger.error(f"Cypher execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "query": query,
                "parameters": parameters or {}
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}",
                "query": query,
                "parameters": parameters or {}
            }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information."""
        try:
            with self.driver.session(database=self.database) as session:
                # Get node labels
                labels_result = session.run("CALL db.labels()")
                labels = [record["label"] for record in labels_result]
                
                # Get relationship types
                rel_types_result = session.run("CALL db.relationshipTypes()")
                relationship_types = [record["relationshipType"] for record in rel_types_result]
                
                # Get property keys
                props_result = session.run("CALL db.propertyKeys()")
                property_keys = [record["propertyKey"] for record in props_result]
                
                # Get constraints
                constraints_result = session.run("SHOW CONSTRAINTS")
                constraints = []
                for record in constraints_result:
                    constraints.append({
                        "name": record.get("name"),
                        "type": record.get("type"),
                        "entityType": record.get("entityType"),
                        "labelsOrTypes": record.get("labelsOrTypes"),
                        "properties": record.get("properties")
                    })
                
                # Get indexes
                indexes_result = session.run("SHOW INDEXES")
                indexes = []
                for record in indexes_result:
                    indexes.append({
                        "name": record.get("name"),
                        "type": record.get("type"),
                        "entityType": record.get("entityType"),
                        "labelsOrTypes": record.get("labelsOrTypes"),
                        "properties": record.get("properties"),
                        "state": record.get("state")
                    })
                
                return {
                    "status": "success",
                    "schema": {
                        "node_labels": labels,
                        "relationship_types": relationship_types,
                        "property_keys": property_keys,
                        "constraints": constraints,
                        "indexes": indexes
                    }
                }
                
        except Exception as e:
            logger.error(f"Schema info retrieval failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def search_nodes(self, label: str = None, properties: Dict[str, Any] = None, limit: int = 100) -> Dict[str, Any]:
        """Search for nodes by label and properties."""
        query_parts = ["MATCH (n"]
        parameters = {}
        
        if label:
            query_parts.append(f":{label}")
        
        query_parts.append(")")
        
        if properties:
            where_conditions = []
            for key, value in properties.items():
                param_name = f"prop_{key}"
                where_conditions.append(f"n.{key} = ${param_name}")
                parameters[param_name] = value
            
            if where_conditions:
                query_parts.append("WHERE " + " AND ".join(where_conditions))
        
        query_parts.append(f"RETURN n LIMIT {limit}")
        query = " ".join(query_parts)
        
        return self.execute_cypher(query, parameters)
    
    def find_shortest_path(self, start_props: Dict[str, Any], end_props: Dict[str, Any], 
                          relationship_types: List[str] = None, max_depth: int = 6) -> Dict[str, Any]:
        """Find shortest path between two nodes."""
        query = "MATCH (start), (end) WHERE "
        
        # Build start node conditions
        start_conditions = []
        parameters = {}
        for key, value in start_props.items():
            param_name = f"start_{key}"
            start_conditions.append(f"start.{key} = ${param_name}")
            parameters[param_name] = value
        
        # Build end node conditions
        end_conditions = []
        for key, value in end_props.items():
            param_name = f"end_{key}"
            end_conditions.append(f"end.{key} = ${param_name}")
            parameters[param_name] = value
        
        query += "(" + " AND ".join(start_conditions) + ") AND (" + " AND ".join(end_conditions) + ")"
        
        # Build path pattern
        if relationship_types:
            rel_pattern = "|".join(relationship_types)
            path_pattern = f"[:{rel_pattern}*1..{max_depth}]"
        else:
            path_pattern = f"[*1..{max_depth}]"
        
        query += f" MATCH path = shortestPath((start)-{path_pattern}-(end)) RETURN path"
        
        return self.execute_cypher(query, parameters)
    
    def get_node_counts(self) -> Dict[str, Any]:
        """Get count of nodes by label."""
        query = """
        MATCH (n)
        RETURN labels(n) as labels, count(n) as count
        ORDER BY count DESC
        """
        return self.execute_cypher(query)
    
    def get_relationship_counts(self) -> Dict[str, Any]:
        """Get count of relationships by type."""
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as relationship_type, count(r) as count
        ORDER BY count DESC
        """
        return self.execute_cypher(query)
    
    def check_connection(self) -> Dict[str, Any]:
        """Check database connection health."""
        try:
            result = self.execute_cypher("RETURN 'connected' as status, datetime() as timestamp")
            if result["status"] == "success":
                return {
                    "status": "healthy",
                    "message": "Neo4j connection is active",
                    "timestamp": result["records"][0]["timestamp"] if result["records"] else None
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": result.get("error", "Unknown error")
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()

# Initialize Neo4j client
neo4j_client = None

# Create MCP server
server = Server("neo4j-mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Neo4j tools."""
    return [
        types.Tool(
            name="neo4j_execute_cypher",
            description="Execute a Cypher query against the Neo4j database",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Cypher query to execute"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Query parameters as key-value pairs",
                        "default": {}
                    },
                    "read_only": {
                        "type": "boolean",
                        "description": "Whether the query is read-only",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="neo4j_get_schema",
            description="Get database schema including labels, relationship types, and constraints",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="neo4j_search_nodes",
            description="Search for nodes by label and properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Node label to filter by"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties to match as key-value pairs"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 100
                    }
                }
            }
        ),
        types.Tool(
            name="neo4j_find_shortest_path",
            description="Find shortest path between two nodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_properties": {
                        "type": "object",
                        "description": "Properties to identify start node"
                    },
                    "end_properties": {
                        "type": "object",
                        "description": "Properties to identify end node"
                    },
                    "relationship_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Allowed relationship types for path"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum path depth",
                        "default": 6
                    }
                },
                "required": ["start_properties", "end_properties"]
            }
        ),
        types.Tool(
            name="neo4j_get_node_counts",
            description="Get count of nodes grouped by label",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="neo4j_get_relationship_counts",
            description="Get count of relationships grouped by type",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="neo4j_check_connection",
            description="Check Neo4j database connection health",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    if not neo4j_client:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": "Neo4j client not initialized"
            }, indent=2)
        )]
    
    try:
        if name == "neo4j_execute_cypher":
            result = neo4j_client.execute_cypher(
                query=arguments["query"],
                parameters=arguments.get("parameters", {}),
                read_only=arguments.get("read_only", True)
            )
            
        elif name == "neo4j_get_schema":
            result = neo4j_client.get_schema_info()
            
        elif name == "neo4j_search_nodes":
            result = neo4j_client.search_nodes(
                label=arguments.get("label"),
                properties=arguments.get("properties"),
                limit=arguments.get("limit", 100)
            )
            
        elif name == "neo4j_find_shortest_path":
            result = neo4j_client.find_shortest_path(
                start_props=arguments["start_properties"],
                end_props=arguments["end_properties"],
                relationship_types=arguments.get("relationship_types"),
                max_depth=arguments.get("max_depth", 6)
            )
            
        elif name == "neo4j_get_node_counts":
            result = neo4j_client.get_node_counts()
            
        elif name == "neo4j_get_relationship_counts":
            result = neo4j_client.get_relationship_counts()
            
        elif name == "neo4j_check_connection":
            result = neo4j_client.check_connection()
            
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
    """Run the Neo4j MCP server."""
    # Initialize Neo4j client from environment variables
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    global neo4j_client
    try:
        neo4j_client = Neo4jClient(neo4j_uri, neo4j_username, neo4j_password, neo4j_database)
        logger.info(f"Starting Neo4j MCP server on http://localhost:8001")
        logger.info(f"Connected to Neo4j at: {neo4j_uri}")
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j client: {e}")
        raise
    
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                NotificationOptions()
            )
    finally:
        if neo4j_client:
            neo4j_client.close()

if __name__ == "__main__":
    asyncio.run(main())