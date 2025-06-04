from typing import Dict, Any, List, Optional, Union
from neo4j import GraphDatabase, Transaction
from neo4j.exceptions import ServiceUnavailable, CypherSyntaxError
from pydantic import BaseModel, Field
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
from ..shared.security import audit_log, require_security_check

logger = structlog.get_logger(__name__)

class Neo4jConfig(BaseModel):
    uri: str = Field(..., description="Neo4j database URI")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    database: str = Field(default="neo4j", description="Database name")
    max_connection_lifetime: int = Field(default=3600, description="Max connection lifetime in seconds")
    max_connection_pool_size: int = Field(default=50, description="Max connection pool size")
    connection_timeout: int = Field(default=30, description="Connection timeout in seconds")
    mcp_url: str = Field(default="http://localhost:8001/mcp", description="Neo4j MCP server URL")
    mcp_transport: str = Field(default="streamable_http", description="MCP transport protocol")

class CypherQuery(BaseModel):
    query: str = Field(..., description="Cypher query string")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    read_only: bool = Field(default=True, description="Whether query is read-only")

class Neo4jTools:
    def __init__(self, config: Neo4jConfig):
        self.config = config
        self.driver = GraphDatabase.driver(
            config.uri,
            auth=(config.username, config.password),
            max_connection_lifetime=config.max_connection_lifetime,
            max_connection_pool_size=config.max_connection_pool_size,
            connection_timeout=config.connection_timeout
        )
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    @audit_log("neo4j_query")
    @require_security_check
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def execute_cypher(self, query: str, parameters: Dict[str, Any] = None, read_only: bool = True) -> Dict[str, Any]:
        try:
            if self._is_dangerous_query(query):
                raise PermissionError(f"Query blocked by security policy: {query}")
            
            parameters = parameters or {}
            
            with self.driver.session(database=self.config.database) as session:
                if read_only:
                    result = session.execute_read(self._run_query, query, parameters)
                else:
                    result = session.execute_write(self._run_query, query, parameters)
                
                return {
                    "status": "success",
                    "data": result,
                    "query": query,
                    "parameters": parameters,
                    "record_count": len(result)
                }
                
        except CypherSyntaxError as e:
            logger.error("Cypher syntax error", error=str(e), query=query)
            return {
                "status": "error",
                "error_type": "syntax_error",
                "error": str(e),
                "query": query
            }
        except ServiceUnavailable as e:
            logger.error("Neo4j service unavailable", error=str(e))
            return {
                "status": "error",
                "error_type": "service_unavailable",
                "error": str(e)
            }
        except Exception as e:
            logger.error("Neo4j query execution failed", error=str(e), query=query)
            return {
                "status": "error",
                "error_type": "execution_error",
                "error": str(e),
                "query": query
            }
    
    def _run_query(self, tx: Transaction, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        result = tx.run(query, parameters)
        return [record.data() for record in result]
    
    def _is_dangerous_query(self, query: str) -> bool:
        dangerous_patterns = [
            "DELETE",
            "REMOVE",
            "DROP",
            "DETACH DELETE",
            "CREATE CONSTRAINT",
            "DROP CONSTRAINT",
            "CREATE INDEX",
            "DROP INDEX"
        ]
        query_upper = query.upper()
        return any(pattern in query_upper for pattern in dangerous_patterns)
    
    @audit_log("neo4j_health_check")
    def check_connection(self) -> Dict[str, Any]:
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                
                return {
                    "status": "healthy",
                    "connection": "successful",
                    "test_query": test_value == 1,
                    "database": self.config.database
                }
        except Exception as e:
            logger.error("Neo4j connection check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "database": self.config.database
            }
    
    @audit_log("neo4j_schema_info")
    def get_schema_info(self) -> Dict[str, Any]:
        try:
            with self.driver.session(database=self.config.database) as session:
                # Get node labels
                labels_result = session.execute_read(
                    self._run_query,
                    "CALL db.labels() YIELD label RETURN collect(label) as labels",
                    {}
                )
                
                # Get relationship types
                rel_types_result = session.execute_read(
                    self._run_query,
                    "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types",
                    {}
                )
                
                # Get property keys
                props_result = session.execute_read(
                    self._run_query,
                    "CALL db.propertyKeys() YIELD propertyKey RETURN collect(propertyKey) as keys",
                    {}
                )
                
                return {
                    "status": "success",
                    "labels": labels_result[0]["labels"] if labels_result else [],
                    "relationship_types": rel_types_result[0]["types"] if rel_types_result else [],
                    "property_keys": props_result[0]["keys"] if props_result else []
                }
                
        except Exception as e:
            logger.error("Failed to retrieve schema info", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    @audit_log("neo4j_node_search")
    def search_nodes(self, label: str = None, properties: Dict[str, Any] = None, limit: int = 100) -> Dict[str, Any]:
        try:
            query_parts = ["MATCH (n"]
            parameters = {}
            
            if label:
                query_parts.append(f":{label}")
            
            if properties:
                prop_conditions = []
                for key, value in properties.items():
                    param_name = f"prop_{key}"
                    prop_conditions.append(f"n.{key} = ${param_name}")
                    parameters[param_name] = value
                
                if prop_conditions:
                    query_parts.extend([" {", ", ".join(prop_conditions), "}"])
            
            query_parts.extend([") RETURN n LIMIT $limit"])
            parameters["limit"] = limit
            
            query = "".join(query_parts)
            
            result = self.execute_cypher(query, parameters, read_only=True)
            
            if result["status"] == "success":
                nodes = []
                for record in result["data"]:
                    node = record["n"]
                    nodes.append({
                        "id": node.id,
                        "labels": list(node.labels),
                        "properties": dict(node)
                    })
                
                result["nodes"] = nodes
                result["node_count"] = len(nodes)
            
            return result
            
        except Exception as e:
            logger.error("Node search failed", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    @audit_log("neo4j_path_query")
    def find_shortest_path(self, start_props: Dict[str, Any], end_props: Dict[str, Any], 
                          relationship_types: List[str] = None, max_depth: int = 6) -> Dict[str, Any]:
        try:
            # Build start and end node patterns
            start_conditions = " AND ".join([f"start.{k} = $start_{k}" for k in start_props.keys()])
            end_conditions = " AND ".join([f"end.{k} = $end_{k}" for k in end_props.keys()])
            
            # Build relationship pattern
            rel_pattern = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_pattern = f"[:{rel_types}*1..{max_depth}]"
            else:
                rel_pattern = f"[*1..{max_depth}]"
            
            query = f"""
            MATCH (start), (end)
            WHERE {start_conditions} AND {end_conditions}
            MATCH path = shortestPath((start)-{rel_pattern}-(end))
            RETURN path, length(path) as pathLength
            ORDER BY pathLength
            LIMIT 10
            """
            
            parameters = {}
            for k, v in start_props.items():
                parameters[f"start_{k}"] = v
            for k, v in end_props.items():
                parameters[f"end_{k}"] = v
            
            result = self.execute_cypher(query, parameters, read_only=True)
            
            if result["status"] == "success" and result["data"]:
                paths = []
                for record in result["data"]:
                    path_data = record["path"]
                    paths.append({
                        "length": record["pathLength"],
                        "nodes": [dict(node) for node in path_data.nodes],
                        "relationships": [dict(rel) for rel in path_data.relationships]
                    })
                
                result["paths"] = paths
                result["path_count"] = len(paths)
            else:
                result["paths"] = []
                result["path_count"] = 0
            
            return result
            
        except Exception as e:
            logger.error("Shortest path query failed", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }