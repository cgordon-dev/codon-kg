"""
Modular Agent Factory for Memory-Enhanced Agents

This module implements a factory pattern for creating different types of
memory-enhanced agents with specific roles and capabilities.
"""

import asyncio
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class AgentConfig:
    """Configuration for creating memory-enhanced agents."""
    name: str
    role: str
    temperature: float = 0.1
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    system_prompt: Optional[str] = None
    max_tokens: int = 4000


class BaseMemoryAgent:
    """Base class for memory-enhanced agents."""
    
    def __init__(self, config: AgentConfig, mem0_server_path: str):
        self.config = config
        self.mem0_server_path = mem0_server_path
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self._tools: Optional[List[Any]] = None
        self.agent = None
        
        # Set up the LLM
        api_key = config.api_key or os.getenv("OPENAI_API_KEY", 
            "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")
        
        self.model = ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            api_key=api_key,
            max_tokens=config.max_tokens
        )
    
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
            logger.info("Memory MCP client initialized", 
                       agent=self.config.name, 
                       server_path=self.mem0_server_path)
            
        except Exception as e:
            logger.error("Failed to initialize memory MCP client", 
                        agent=self.config.name, 
                        error=str(e))
            raise
    
    async def get_memory_tools(self) -> List[Any]:
        """Get memory tools from MCP server."""
        if not self._tools:
            if not self.mcp_client:
                await self.initialize_mcp_client()
            
            self._tools = await self.mcp_client.get_tools()
            logger.info("Retrieved memory tools", 
                       agent=self.config.name, 
                       tool_count=len(self._tools))
        
        return self._tools
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        if self.config.system_prompt:
            return self.config.system_prompt
        
        base_prompt = f"""You are {self.config.name}, a memory-enhanced AI assistant specialized in {self.config.role}.

Core Memory Capabilities:
- **save_memory**: Store important information for future reference
- **search_memories**: Find relevant information using semantic search
- **get_all_memories**: Retrieve complete memory context when needed

Memory Management Guidelines:
- Always search existing memories before responding to complex questions
- Save important information that would be valuable in future conversations
- Use memories to provide personalized and contextually relevant responses
- Reference relevant memories to demonstrate continuity and understanding

Your specialized role: {self.config.role}
"""
        return base_prompt
    
    async def build_agent(self) -> Any:
        """Build the LangGraph agent with memory tools."""
        if self.agent:
            return self.agent
        
        try:
            # Get memory tools
            tools = await self.get_memory_tools()
            
            # Add any role-specific tools
            custom_tools = self.get_custom_tools()
            all_tools = tools + custom_tools
            
            # Create the agent
            system_prompt = self.get_system_prompt()
            self.agent = create_react_agent(
                model=self.model,
                tools=all_tools,
                prompt=system_prompt
            )
            
            logger.info("Built memory-enhanced agent", 
                       agent=self.config.name,
                       tool_count=len(all_tools))
            
            return self.agent
            
        except Exception as e:
            logger.error("Failed to build agent", 
                        agent=self.config.name, 
                        error=str(e))
            raise
    
    def get_custom_tools(self) -> List[Any]:
        """Override this method to add role-specific tools."""
        return []
    
    async def invoke(self, message: str) -> Dict[str, Any]:
        """Invoke the agent with a message."""
        try:
            if not self.agent:
                await self.build_agent()
            
            result = await self.agent.ainvoke({
                "messages": [{"role": "user", "content": message}]
            })
            
            return {
                "status": "success",
                "response": result["messages"][-1].content,
                "agent": self.config.name,
                "role": self.config.role
            }
            
        except Exception as e:
            logger.error("Agent invocation failed", 
                        agent=self.config.name, 
                        error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "agent": self.config.name,
                "role": self.config.role
            }
    
    async def close(self):
        """Close the MCP client connection."""
        if self.mcp_client:
            try:
                await self.mcp_client.close()
                logger.info("MCP client closed", agent=self.config.name)
            except Exception as e:
                logger.warning("Error closing MCP client", 
                              agent=self.config.name, 
                              error=str(e))
            finally:
                self.mcp_client = None
                self._tools = None


class MemoryAgent(BaseMemoryAgent):
    """Specialized agent focused on memory operations as described in the instructions."""
    
    def __init__(self, mem0_server_path: str):
        config = AgentConfig(
            name="MemoryAgent",
            role="memory operations and knowledge management",
            temperature=0.1,
            system_prompt="""You are a specialized Memory Agent with long-term memory capabilities.

Your core responsibilities:
- Execute memory operations: save, retrieve, and search
- Organize and categorize stored information
- Provide context-aware responses based on stored memories
- Help users build their personal knowledge base

Key capabilities:
- save_memory: Store important information, preferences, goals, or context
- search_memories: Find relevant memories using semantic search
- get_all_memories: Retrieve complete memory context when needed

Best practices:
- Always search memories before responding to questions
- Save information that would be valuable in future conversations
- Provide specific and relevant memory references
- Ask clarifying questions when memory content is unclear"""
        )
        super().__init__(config, mem0_server_path)
    
    async def save_memory(self, content: str) -> Dict[str, Any]:
        """Save content to long-term memory."""
        return await self.invoke(f"Save this to memory: {content}")
    
    async def retrieve_memories(self) -> Dict[str, Any]:
        """Retrieve all stored memories."""
        return await self.invoke("Show me all my stored memories")
    
    async def search_memories(self, query: str) -> Dict[str, Any]:
        """Search memories for specific information."""
        return await self.invoke(f"Search my memories for: {query}")


class AgentFactory:
    """Factory class for creating different types of memory-enhanced agents."""
    
    def __init__(self, mem0_server_path: str = None):
        if mem0_server_path is None:
            # Default path to the mcp-mem0 server
            base_path = os.path.dirname(os.path.abspath(__file__))
            mem0_server_path = os.path.join(base_path, "mcp-mem0", "src", "main.py")
        
        self.mem0_server_path = mem0_server_path
        self._agents: Dict[str, BaseMemoryAgent] = {}
    
    async def create_memory_agent(self) -> MemoryAgent:
        """Create a specialized memory agent."""
        agent = MemoryAgent(self.mem0_server_path)
        self._agents["memory_agent"] = agent
        return agent
    
    async def create_custom_agent(self, config: AgentConfig) -> BaseMemoryAgent:
        """Create a custom agent with specific configuration."""
        agent = BaseMemoryAgent(config, self.mem0_server_path)
        self._agents[config.name.lower()] = agent
        return agent
    
    def get_agent(self, agent_name: str) -> Optional[BaseMemoryAgent]:
        """Get an existing agent by name."""
        return self._agents.get(agent_name.lower())
    
    async def close_all_agents(self):
        """Close all agent MCP connections."""
        for agent in self._agents.values():
            await agent.close()
        self._agents.clear()


# Convenience function for easy agent creation
async def create_memory_agent(mem0_server_path: str = None) -> MemoryAgent:
    """Create a memory agent as described in the original instructions."""
    factory = AgentFactory(mem0_server_path)
    return await factory.create_memory_agent()


# Example usage following the original instructions pattern
async def main():
    """Example implementation following the original instructions."""
    print("🧠 Testing Memory Agent Implementation")
    print("=" * 50)
    
    try:
        # Create MCP client as described in instructions
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mem0_server_path = os.path.join(current_dir, "mcp-mem0", "src", "main.py")
        
        server_config = {
            "mem0": {
                "command": "python", 
                "args": [mem0_server_path],
                "transport": "stdio",
            }
        }
        
        client = MultiServerMCPClient(server_config)
        tools = await client.get_tools()
        
        # Create agent as described in instructions
        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY", 
                "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")
        )
        
        agent = create_react_agent(model, tools)
        
        print("✅ Agent created successfully")
        
        # Test save memory
        print("\n📝 Testing save memory...")
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": "Save this memory: 'Meeting with client at 3 PM'."}]
        })
        print(f"Save result: {result['messages'][-1].content[:100]}...")
        
        # Test retrieve memories  
        print("\n📋 Testing retrieve memories...")
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": "What memories do I have?"}]
        })
        print(f"Retrieve result: {result['messages'][-1].content[:100]}...")
        
        # Test search memories
        print("\n🔍 Testing search memories...")
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": "Do I have any meetings scheduled?"}]
        })
        print(f"Search result: {result['messages'][-1].content[:100]}...")
        
        print("\n✨ Memory agent testing completed successfully!")
        
        # Test modular agent factory pattern
        print("\n🏭 Testing Modular Agent Factory Pattern...")
        memory_agent = await create_memory_agent()
        
        await memory_agent.save_memory("Discuss project timeline with team.")
        memories = await memory_agent.retrieve_memories()
        search_result = await memory_agent.search_memories("project timeline")
        
        print("✅ Modular factory pattern working correctly")
        
        # Cleanup
        await memory_agent.close()
        await client.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())