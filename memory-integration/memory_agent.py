"""
Memory-Enhanced Agent using MCP-Mem0 Integration

This module implements a LangGraph agent that can save, retrieve, and search
long-term memories using the mcp-mem0 server through the Model Context Protocol.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
from langchain_mcp_adapters.client import MultiServerMCPClient
import structlog
import os
import sys

# Add the agents path to import from the main project
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from shared.base_agent import BaseAgent, AgentConfig, BaseAgentState
from shared.llm_factory import LLMFactory
from shared.langsmith_tracing import get_tracer, create_langsmith_tags, create_langsmith_metadata
from config.settings import get_config

logger = structlog.get_logger(__name__)

class MemoryEnhancedAgent(BaseAgent):
    """Agent with long-term memory capabilities using mcp-mem0."""
    
    def __init__(self, config: AgentConfig, mem0_server_path: str):
        super().__init__(config)
        self.mem0_server_path = mem0_server_path
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self._mcp_tools: Optional[List[Any]] = None
        
        # Get global config and create LLM
        global_config = get_config()
        self.model = LLMFactory.create_llm(global_config.llm, global_config.langsmith)
    
    def __del__(self):
        """Cleanup MCP client on deletion."""
        if hasattr(self, 'mcp_client') and self.mcp_client:
            try:
                asyncio.run(self.mcp_client.close())
            except Exception:
                pass
    
    async def initialize_mcp_client(self) -> None:
        """Initialize the MCP client connection to mem0 server."""
        try:
            server_config = {
                "mem0": {
                    "command": "python",
                    "args": [self.mem0_server_path],
                    "transport": "stdio",
                }
            }
            
            self.mcp_client = MultiServerMCPClient(server_config)
            logger.info("Memory MCP client initialized", server_path=self.mem0_server_path)
            
        except Exception as e:
            logger.error("Failed to initialize memory MCP client", error=str(e))
            raise
    
    async def get_mcp_tools(self) -> List[Any]:
        """Get memory tools from MCP server."""
        if not self._mcp_tools:
            if not self.mcp_client:
                await self.initialize_mcp_client()
            
            self._mcp_tools = await self.mcp_client.get_tools()
            logger.info("Retrieved memory MCP tools", tool_count=len(self._mcp_tools))
        
        return self._mcp_tools
    
    def create_tools(self) -> List[Any]:
        """Create tools including memory capabilities."""
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
            
            logger.info("Retrieved memory MCP tools", tool_count=len(mcp_tools))
            
            # Add any additional custom tools here
            custom_tools = self._create_custom_tools()
            
            return mcp_tools + custom_tools
            
        except Exception as e:
            logger.error("Failed to get MCP tools, using fallback", error=str(e))
            # Fallback to custom tools only if MCP fails
            return self._create_custom_tools()
    
    def _create_custom_tools(self) -> List[Any]:
        """Create custom tools for the memory agent."""
        
        @tool
        def analyze_conversation_context() -> str:
            """Analyze the current conversation context to identify important information worth remembering."""
            return json.dumps({
                "status": "success",
                "analysis": "This tool helps identify key information in conversations that should be saved to memory.",
                "suggestions": [
                    "Look for personal preferences and settings",
                    "Note important dates and appointments", 
                    "Remember project details and requirements",
                    "Track user goals and objectives"
                ]
            })
        
        @tool 
        def memory_summary() -> str:
            """Provide a summary of what types of memories are typically stored."""
            return json.dumps({
                "status": "success",
                "memory_types": [
                    "Personal preferences and settings",
                    "Project information and requirements", 
                    "Important dates and appointments",
                    "User goals and objectives",
                    "Past conversation context",
                    "Technical configurations"
                ],
                "usage": "Use save_memory to store important information, search_memories to find relevant context, and get_all_memories for full context."
            })
        
        return [analyze_conversation_context, memory_summary]
    
    def build_graph(self) -> Any:
        """Build the LangGraph workflow for the memory-enhanced agent."""
        tools = self.create_tools()
        
        system_prompt = """You are a memory-enhanced AI assistant with long-term memory capabilities. Your core responsibilities include:

1. **Memory Management**: Proactively save important information to long-term memory and retrieve relevant context
2. **Contextual Awareness**: Use stored memories to provide personalized and contextually relevant responses
3. **Information Synthesis**: Combine current conversation with historical memory to deliver comprehensive assistance

Key Memory Capabilities:
- **save_memory**: Store important information, preferences, goals, or context for future reference
- **search_memories**: Find relevant memories using semantic search based on the current conversation
- **get_all_memories**: Retrieve complete memory context when comprehensive understanding is needed

Memory Management Guidelines:
- Always search existing memories at the start of conversations to understand context
- Save important user preferences, goals, project details, and significant information
- Update memories when information changes or becomes outdated
- Use memories to provide personalized recommendations and continuity

Best Practices:
- Proactively search memories before responding to complex questions
- Save information that would be valuable in future conversations
- Reference relevant memories to demonstrate continuity and understanding
- Ask clarifying questions if memories seem outdated or conflicting

When to Save Memories:
- User shares personal preferences or settings
- Important project details or requirements are discussed
- Goals, objectives, or priorities are mentioned
- Technical configurations or setup information is provided
- Significant dates, appointments, or deadlines are noted

Memory Search Strategy:
- Search for relevant context before providing recommendations
- Use specific keywords related to the current topic
- Consider both direct matches and related concepts
- Leverage memories to provide more informed responses

Your responses should demonstrate awareness of past interactions and use stored memories to provide continuity and personalization. Always prioritize user privacy and only store information that would be helpful for future assistance."""

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
        """Execute the memory-enhanced agent with user input."""
        # Setup LangSmith session for this run
        tracer = get_tracer()
        session_name = f"memory-agent-{hash(user_input) % 10000}"
        
        if tracer and tracer.is_enabled():
            tracer.set_session(session_name)
            self.logger.info("LangSmith session set", session=session_name)
        
        try:
            graph = self.build_graph()
            initial_state = self.get_initial_state()
            
            if context:
                initial_state["context"].update(context)
            
            # Add LangSmith metadata
            langsmith_metadata = create_langsmith_metadata({
                "agent": "memory-enhanced",
                "query": user_input[:100],  # Truncate for metadata
                "session": session_name,
                "context_keys": list(context.keys()) if context else []
            })
            initial_state["metadata"].update(langsmith_metadata)
            
            inputs = {
                "messages": [HumanMessage(content=user_input)],
                "metadata": initial_state["metadata"],
                "context": initial_state["context"],
                "error_count": 0,
                "max_retries": self.config.max_retries
            }
            
            self.logger.info("Starting memory-enhanced agent execution", 
                           input=user_input, 
                           session=session_name)
            
            result = graph.invoke(inputs)
            
            response_data = {
                "status": "success",
                "response": result["messages"][-1].content if result["messages"] else "No response",
                "metadata": result.get("metadata", {}),
                "context": result.get("context", {}),
                "langsmith_session": session_name if tracer and tracer.is_enabled() else None
            }
            
            self.logger.info("Memory-enhanced agent execution completed", 
                           status="success", 
                           session=session_name)
            
            return response_data
            
        except Exception as e:
            self.logger.error("Memory-enhanced agent execution failed", 
                            error=str(e), 
                            session=session_name)
            return {
                "status": "error",
                "error": str(e),
                "response": "I encountered an error while processing your request.",
                "langsmith_session": session_name if tracer and tracer.is_enabled() else None
            }
        finally:
            # Clear session after execution
            if tracer and tracer.is_enabled():
                tracer.clear_session()
    
    async def close(self):
        """Close the MCP client connection."""
        if self.mcp_client:
            await self.mcp_client.close()
            self.mcp_client = None
            self._mcp_tools = None


# Agent factory functions for easy instantiation
def create_memory_agent(mem0_server_path: str = None) -> MemoryEnhancedAgent:
    """Factory function to create a memory-enhanced agent."""
    if mem0_server_path is None:
        # Default path to the mcp-mem0 server in this project
        base_path = os.path.dirname(os.path.abspath(__file__))
        mem0_server_path = os.path.join(base_path, "mcp-mem0", "src", "main.py")
    
    config = AgentConfig(
        name="memory-enhanced-agent",
        model_name="gpt-4o-mini",
        temperature=0.1,
        max_tokens=4000,
        timeout=300,
        max_retries=3,
        system_prompt="You are a memory-enhanced AI assistant with long-term memory capabilities."
    )
    
    return MemoryEnhancedAgent(config, mem0_server_path)


# Convenience class for specific memory use cases
class MemoryAgent(MemoryEnhancedAgent):
    """Specialized agent focused on memory operations."""
    
    async def save_memory(self, content: str) -> Dict[str, Any]:
        """Save content to long-term memory."""
        result = self.run(f"Save this important information to memory: {content}")
        return result
    
    async def retrieve_memories(self) -> Dict[str, Any]:
        """Retrieve all stored memories."""
        result = self.run("Please show me all my stored memories.")
        return result
    
    async def search_memories(self, query: str) -> Dict[str, Any]:
        """Search memories for specific information."""
        result = self.run(f"Search my memories for information about: {query}")
        return result


if __name__ == "__main__":
    # Example usage
    async def main():
        agent = create_memory_agent()
        
        # Test saving a memory
        result1 = agent.run("Save this to memory: I prefer dark mode for all applications.")
        print("Save Memory Result:", result1)
        
        # Test searching memories
        result2 = agent.run("What do I prefer for application themes?")
        print("Search Memory Result:", result2)
        
        # Cleanup
        await agent.close()
    
    # Uncomment to test
    # asyncio.run(main())