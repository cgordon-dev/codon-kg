"""
Base Agent Class for Memory-Enhanced LangGraph Agents
"""

import asyncio
import structlog
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage

from config import get_config

logger = structlog.get_logger(__name__)

class BaseAgent(ABC):
    """Base class for memory-enhanced LangGraph agents."""
    
    def __init__(self, name: str, model: str = None):
        self.name = name
        self.config = get_config()
        self.model = model or self.config.langgraph.agent_model
        self.mcp_client = None
        self.tools = []
        self.agent = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the agent with MCP tools."""
        if self._initialized:
            return
        
        try:
            # Set up MCP client for memory tools
            self.mcp_client = MultiServerMCPClient({
                "mem0": {
                    "command": self.config.memory.mcp_command,
                    "args": [self.config.memory.mcp_script_path],
                    "transport": self.config.memory.mcp_transport,
                }
            })
            
            # Get memory tools
            memory_tools = await self.mcp_client.get_tools()
            logger.info(f"Loaded {len(memory_tools)} memory tools", agent=self.name)
            
            # Get agent-specific tools
            agent_tools = await self.get_agent_tools()
            
            # Combine all tools
            self.tools = memory_tools + agent_tools
            
            # Create the agent
            self.agent = create_react_agent(
                self.model, 
                self.tools,
                state_modifier=self.get_state_modifier()
            )
            
            self._initialized = True
            logger.info("Agent initialized successfully", agent=self.name, tool_count=len(self.tools))
            
        except Exception as e:
            logger.error("Failed to initialize agent", agent=self.name, error=str(e))
            raise
    
    @abstractmethod
    async def get_agent_tools(self) -> List[Any]:
        """Get agent-specific tools. Must be implemented by subclasses."""
        pass
    
    def get_state_modifier(self) -> str:
        """Get state modifier prompt for the agent."""
        return f"""You are {self.name}, an AI assistant with access to long-term memory capabilities.

Key capabilities:
1. **Memory Management**: You can save, retrieve, and search through memories using the available memory tools
2. **Context Awareness**: Always check for relevant memories before responding to queries
3. **Learning**: Save important information from conversations for future reference

Memory Tools Available:
- save_memory: Save important information for later recall
- get_all_memories: Retrieve all saved memories
- search_memories: Search for specific memories using natural language

Instructions:
1. For each user query, first search for relevant memories using search_memories
2. Use retrieved memories to provide more personalized and contextual responses
3. Save new important information using save_memory when appropriate
4. Be transparent about what you remember and what you're learning

Always be helpful, accurate, and maintain user privacy when handling memories."""
    
    async def invoke(self, message: str, session_id: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke the agent with a message."""
        if not self._initialized:
            await self.initialize()
        
        session_id = session_id or self.config.langgraph.default_session_id
        
        try:
            # Prepare the input
            messages = [HumanMessage(content=message)]
            
            # Add context if provided
            if context:
                context_message = f"Context: {context}"
                messages.insert(0, HumanMessage(content=context_message))
            
            # Invoke the agent
            response = await self.agent.ainvoke({
                "messages": messages,
                "session_id": session_id
            })
            
            # Extract the response
            if response and "messages" in response:
                last_message = response["messages"][-1]
                response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response_content = "No response generated"
            
            # Auto-save interaction if enabled
            if self.config.langgraph.auto_save_interactions:
                await self._auto_save_interaction(message, response_content, session_id)
            
            return {
                "status": "success",
                "response": response_content,
                "session_id": session_id,
                "agent": self.name
            }
            
        except Exception as e:
            logger.error("Agent invocation failed", agent=self.name, error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name
            }
    
    async def _auto_save_interaction(self, user_message: str, agent_response: str, session_id: str):
        """Automatically save important interactions to memory."""
        try:
            # Simple heuristic: save if the interaction contains certain keywords or is substantial
            important_keywords = [
                "remember", "save", "important", "meeting", "deadline", 
                "appointment", "task", "project", "goal", "preference"
            ]
            
            combined_text = f"{user_message} {agent_response}".lower()
            
            if (any(keyword in combined_text for keyword in important_keywords) or 
                len(user_message + agent_response) > 200):
                
                memory_content = f"Session {session_id}: User asked '{user_message}' and I responded with '{agent_response[:200]}...'"
                
                # Use the save_memory tool if available
                save_tool = next((tool for tool in self.tools if 'save' in tool.name.lower() and 'memory' in tool.name.lower()), None)
                if save_tool:
                    await save_tool.arun(content=memory_content)
                    logger.debug("Auto-saved interaction", session=session_id)
        
        except Exception as e:
            logger.warning("Failed to auto-save interaction", error=str(e))
    
    async def save_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Save a memory with optional metadata."""
        if not self._initialized:
            await self.initialize()
        
        try:
            save_message = f"Save this memory: '{content}'"
            if metadata:
                save_message += f" with metadata: {metadata}"
            
            response = await self.invoke(save_message)
            return response.get("response", "Memory saved successfully")
            
        except Exception as e:
            logger.error("Failed to save memory", error=str(e))
            return f"Error saving memory: {str(e)}"
    
    async def retrieve_memories(self, query: str = None) -> str:
        """Retrieve memories, optionally filtered by query."""
        if not self._initialized:
            await self.initialize()
        
        try:
            if query:
                message = f"Search for memories about: {query}"
            else:
                message = "What memories do I have?"
            
            response = await self.invoke(message)
            return response.get("response", "No memories found")
            
        except Exception as e:
            logger.error("Failed to retrieve memories", error=str(e))
            return f"Error retrieving memories: {str(e)}"
    
    async def search_memories(self, query: str) -> str:
        """Search memories using natural language query."""
        if not self._initialized:
            await self.initialize()
        
        try:
            message = f"Do I have any memories about '{query}'?"
            response = await self.invoke(message)
            return response.get("response", "No relevant memories found")
            
        except Exception as e:
            logger.error("Failed to search memories", error=str(e))
            return f"Error searching memories: {str(e)}"
    
    async def close(self):
        """Clean up resources."""
        if self.mcp_client:
            try:
                await self.mcp_client.close()
            except:
                pass
        logger.info("Agent closed", agent=self.name)
    
    def __del__(self):
        """Cleanup on deletion."""
        if self.mcp_client and not self.mcp_client.closed:
            try:
                asyncio.create_task(self.close())
            except:
                pass