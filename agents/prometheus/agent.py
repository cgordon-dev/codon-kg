from typing import List, Dict, Any
import asyncio
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
import structlog

from shared.base_agent import BaseAgent, AgentConfig, BaseAgentState
from shared.mcp_client import create_mcp_client
from shared.llm_factory import LLMFactory
from config.settings import get_config
from .tools import PrometheusConfig

logger = structlog.get_logger(__name__)

class PrometheusAgent(BaseAgent):
    def __init__(self, config: AgentConfig, prometheus_config: PrometheusConfig):
        super().__init__(config)
        self.prometheus_config = prometheus_config
        self.mcp_client = create_mcp_client(
            prometheus_config={
                "url": prometheus_config.mcp_url,
                "transport": prometheus_config.mcp_transport
            },
            neo4j_config={}  # Not used in Prometheus agent
        )
        global_config = get_config()
        self.model = LLMFactory.create_llm(global_config.llm, global_config.langsmith)
        self._mcp_tools = None
    
    async def get_mcp_tools(self) -> List[Any]:
        """Get Prometheus tools from MCP server."""
        if not self._mcp_tools:
            await self.mcp_client.initialize()
            self._mcp_tools = await self.mcp_client.get_prometheus_tools()
        return self._mcp_tools
    
    def create_tools(self) -> List[Any]:
        """Create tools using MCP client."""
        try:
            # Get MCP tools asynchronously
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a new event loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.get_mcp_tools())
                    mcp_tools = future.result()
            else:
                mcp_tools = loop.run_until_complete(self.get_mcp_tools())
            
            logger.info("Retrieved Prometheus MCP tools", tool_count=len(mcp_tools))
            return mcp_tools
            
        except Exception as e:
            logger.error("Failed to get MCP tools, falling back to legacy implementation", error=str(e))
            # Fallback to original implementation if MCP fails
            return self._create_fallback_tools()
    
    def _create_fallback_tools(self) -> List[Any]:
        """Fallback tools implementation if MCP is unavailable."""
        from .tools import PrometheusTools
        
        prometheus_tools = PrometheusTools(self.prometheus_config)
        
        @tool
        def query_prometheus_metrics(metric_query: str, time_range: str = None) -> str:
            """Query Prometheus metrics using PromQL."""
            result = prometheus_tools.query_prometheus(metric_query, time_range)
            return str(result)
        
        @tool
        def check_prometheus_health() -> str:
            """Check if Prometheus server is healthy and responsive."""
            result = prometheus_tools.check_prometheus_health()
            return str(result)
        
        @tool
        def get_active_alerts() -> str:
            """Retrieve all currently active/firing alerts from Prometheus."""
            result = prometheus_tools.get_active_alerts()
            return str(result)
        
        @tool
        def detect_metric_anomalies(metric: str, threshold: float = 2.0) -> str:
            """Detect anomalies in a specific metric using statistical analysis."""
            result = prometheus_tools.detect_anomalies(metric, threshold)
            return str(result)
        
        return [
            query_prometheus_metrics,
            check_prometheus_health,
            get_active_alerts,
            detect_metric_anomalies
        ]
    
    def build_graph(self) -> Any:
        tools = self.create_tools()
        
        system_prompt = """You are a Prometheus monitoring specialist agent. Your responsibilities include:

1. **Metrics Analysis**: Query and analyze Prometheus metrics using PromQL
2. **Health Monitoring**: Check system and service health status
3. **Alert Management**: Monitor and respond to active alerts
4. **Anomaly Detection**: Identify unusual patterns in metrics data

Key capabilities:
- Execute PromQL queries for instant and range data
- Perform statistical anomaly detection on metrics
- Monitor alert status and escalation
- Provide actionable insights based on metrics data

Guidelines:
- Always validate metric names and query syntax
- Provide context and interpretation for metric values
- Suggest remediation steps for detected issues
- Use appropriate time ranges for historical analysis
- Be concise but thorough in your analysis

When querying metrics, consider:
- Rate vs counter vs gauge metric types
- Appropriate aggregation functions (avg, sum, max, etc.)
- Time window selection for rate calculations
- Labels for filtering and grouping

Respond with clear, actionable insights based on the monitoring data."""

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
        """Execute the Prometheus monitoring agent with user input."""
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
            
            self.logger.info("Starting Prometheus agent execution", input=user_input)
            
            result = graph.invoke(inputs)
            
            return {
                "status": "success",
                "response": result["messages"][-1].content if result["messages"] else "No response",
                "metadata": result.get("metadata", {}),
                "context": result.get("context", {})
            }
            
        except Exception as e:
            self.logger.error("Prometheus agent execution failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "response": "I encountered an error while processing your request."
            }