from typing import List, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
import structlog
import json

from ..shared.base_agent import BaseAgent, AgentConfig, BaseAgentState
from .tools import Neo4jTools, Neo4jConfig

logger = structlog.get_logger(__name__)

class Neo4jAgent(BaseAgent):
    def __init__(self, config: AgentConfig, neo4j_config: Neo4jConfig):
        super().__init__(config)
        self.neo4j_tools = Neo4jTools(neo4j_config)
        self.model = ChatAnthropic(
            model_name=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
    
    def __del__(self):
        if hasattr(self, 'neo4j_tools'):
            self.neo4j_tools.close()
    
    def create_tools(self) -> List[Any]:
        @tool
        def execute_cypher_query(query: str, parameters: str = None, read_only: bool = True) -> str:
            """
            Execute a Cypher query against the Neo4j knowledge graph.
            
            Args:
                query: Cypher query string (e.g., 'MATCH (n:Person) RETURN n.name LIMIT 10')
                parameters: JSON string of query parameters (optional)
                read_only: Whether the query is read-only (default: True)
            
            Returns:
                JSON string with query results and metadata
            """
            try:
                params = json.loads(parameters) if parameters else {}
            except json.JSONDecodeError:
                return json.dumps({
                    "status": "error",
                    "error": "Invalid JSON parameters"
                })
            
            result = self.neo4j_tools.execute_cypher(query, params, read_only)
            return json.dumps(result, default=str)
        
        @tool
        def check_neo4j_connection() -> str:
            """
            Check if Neo4j database connection is healthy and responsive.
            
            Returns:
                JSON string with connection status and details
            """
            result = self.neo4j_tools.check_connection()
            return json.dumps(result, default=str)
        
        @tool
        def get_database_schema() -> str:
            """
            Retrieve the Neo4j database schema including node labels, relationships, and properties.
            
            Returns:
                JSON string with schema information
            """
            result = self.neo4j_tools.get_schema_info()
            return json.dumps(result, default=str)
        
        @tool
        def search_nodes_by_properties(label: str = None, properties: str = None, limit: int = 100) -> str:
            """
            Search for nodes in the knowledge graph by label and/or properties.
            
            Args:
                label: Node label to filter by (optional)
                properties: JSON string of properties to match (optional)
                limit: Maximum number of nodes to return (default: 100)
            
            Returns:
                JSON string with matching nodes and their properties
            """
            try:
                props = json.loads(properties) if properties else None
            except json.JSONDecodeError:
                return json.dumps({
                    "status": "error",
                    "error": "Invalid JSON properties"
                })
            
            result = self.neo4j_tools.search_nodes(label, props, limit)
            return json.dumps(result, default=str)
        
        @tool
        def find_shortest_path_between_nodes(start_properties: str, end_properties: str, 
                                           relationship_types: str = None, max_depth: int = 6) -> str:
            """
            Find the shortest path between two nodes in the knowledge graph.
            
            Args:
                start_properties: JSON string of properties to identify start node
                end_properties: JSON string of properties to identify end node
                relationship_types: JSON array of relationship types to consider (optional)
                max_depth: Maximum path depth to search (default: 6)
            
            Returns:
                JSON string with shortest paths and their details
            """
            try:
                start_props = json.loads(start_properties)
                end_props = json.loads(end_properties)
                rel_types = json.loads(relationship_types) if relationship_types else None
            except json.JSONDecodeError:
                return json.dumps({
                    "status": "error",
                    "error": "Invalid JSON in parameters"
                })
            
            result = self.neo4j_tools.find_shortest_path(start_props, end_props, rel_types, max_depth)
            return json.dumps(result, default=str)
        
        return [
            execute_cypher_query,
            check_neo4j_connection,
            get_database_schema,
            search_nodes_by_properties,
            find_shortest_path_between_nodes
        ]
    
    def build_graph(self) -> Any:
        tools = self.create_tools()
        
        system_prompt = """You are a Neo4j knowledge graph specialist agent. Your responsibilities include:

1. **Graph Querying**: Execute Cypher queries to retrieve and analyze graph data
2. **Schema Management**: Understand and navigate the graph schema
3. **Relationship Analysis**: Discover connections and patterns between entities
4. **Data Exploration**: Search and filter nodes based on properties and relationships

Key capabilities:
- Execute read-only and write Cypher queries safely
- Navigate complex graph structures and relationships
- Perform path finding and graph traversal operations
- Analyze node properties and relationship patterns
- Provide insights based on graph topology

Cypher Query Guidelines:
- Use MATCH clauses for pattern matching
- Apply WHERE conditions for filtering
- Use RETURN to specify output fields
- Leverage relationship patterns like (a)-[:REL_TYPE]->(b)
- Use aggregation functions (COUNT, SUM, AVG) for analytics
- Apply LIMIT for result pagination

Security Considerations:
- Only execute approved read operations by default
- Validate all input parameters
- Avoid destructive operations unless explicitly requested
- Use parameterized queries to prevent injection

Best Practices:
- Start with schema exploration for new databases
- Use specific node labels and relationship types when possible
- Optimize queries with appropriate indexes
- Consider performance implications of complex traversals
- Provide clear explanations of graph patterns found

When analyzing results:
- Interpret node relationships and their meanings
- Identify key entities and their connections
- Suggest follow-up queries for deeper analysis
- Explain graph patterns in business terms"""

        agent = create_react_agent(
            model=self.model,
            tools=tools,
            prompt=system_prompt
        )
        
        graph_builder = StateGraph(BaseAgentState)
        graph_builder.add_node("agent", agent)
        graph_builder.set_entry_point("agent")
        graph_builder.add_edge("agent", END)
        
        return graph_builder.compile()
    
    def run(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the Neo4j knowledge graph agent with user input."""
        try:
            graph = self.build_graph()
            initial_state = self.get_initial_state()
            
            if context:
                initial_state["context"].update(context)
            
            inputs = {
                "messages": [HumanMessage(content=user_input)],
                "metadata": initial_state["metadata"],
                "context": initial_state["context"],
                "error_count": 0,
                "max_retries": self.config.max_retries
            }
            
            self.logger.info("Starting Neo4j agent execution", input=user_input)
            
            result = graph.invoke(inputs)
            
            return {
                "status": "success",
                "response": result["messages"][-1].content if result["messages"] else "No response",
                "metadata": result.get("metadata", {}),
                "context": result.get("context", {})
            }
            
        except Exception as e:
            self.logger.error("Neo4j agent execution failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "response": "I encountered an error while processing your request."
            }
    
    def close(self):
        """Close the Neo4j connection."""
        if hasattr(self, 'neo4j_tools'):
            self.neo4j_tools.close()