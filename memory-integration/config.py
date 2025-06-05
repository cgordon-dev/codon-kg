"""
Configuration for Memory Integration
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MemoryConfig(BaseModel):
    """Configuration for Mem0 memory service."""
    
    # MCP Server Configuration
    mcp_command: str = Field(default="python")
    mcp_script_path: str = Field(default=str(Path(__file__).parent / "mcp-mem0" / "src" / "main.py"))
    mcp_transport: str = Field(default="stdio")
    
    # Database Configuration
    database_url: str = Field(default=os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/mem0db"))
    
    # LLM Configuration (inherited from main system)
    llm_provider: str = Field(default=os.getenv("LLM_PROVIDER", "openai"))
    llm_api_key: str = Field(default=os.getenv("OPENAI_API_KEY", ""))
    llm_model: str = Field(default=os.getenv("LLM_CHOICE", "gpt-4o-mini"))
    llm_base_url: str = Field(default=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"))
    
    # Embedding Configuration
    embedding_model: str = Field(default=os.getenv("EMBEDDING_MODEL_CHOICE", "text-embedding-3-small"))
    
    # Memory Settings
    memory_collection_name: str = Field(default="codon_kg_memories")
    max_memory_items: int = Field(default=1000)
    memory_ttl_days: Optional[int] = Field(default=None)  # None means no expiration

class LangGraphConfig(BaseModel):
    """Configuration for LangGraph agent integration."""
    
    # Agent Configuration
    agent_model: str = Field(default="openai:gpt-4o-mini")
    agent_temperature: float = Field(default=0.1)
    max_iterations: int = Field(default=10)
    
    # Memory Integration
    enable_memory: bool = Field(default=True)
    memory_context_limit: int = Field(default=5)  # Number of relevant memories to include
    
    # Session Management
    default_session_id: str = Field(default="default")
    auto_save_interactions: bool = Field(default=True)

class IntegrationConfig(BaseModel):
    """Main configuration for memory integration."""
    
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    langgraph: LangGraphConfig = Field(default_factory=LangGraphConfig)
    
    # Logging
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    enable_debug: bool = Field(default=os.getenv("DEBUG", "false").lower() == "true")
    
    def validate_config(self) -> dict:
        """Validate configuration and return any issues."""
        issues = []
        
        # Check required API keys
        if not self.memory.llm_api_key:
            issues.append("LLM API key is required")
        
        # Check MCP script path
        mcp_path = Path(self.memory.mcp_script_path)
        if not mcp_path.exists():
            issues.append(f"MCP script not found at: {mcp_path}")
        
        # Check database URL format
        if not self.memory.database_url.startswith(('postgresql://', 'sqlite://')):
            issues.append("DATABASE_URL must be a valid PostgreSQL or SQLite URL")
        
        return {
            "status": "valid" if not issues else "invalid",
            "issues": issues
        }

# Global configuration instance
config = IntegrationConfig()

def get_config() -> IntegrationConfig:
    """Get the global configuration instance."""
    return config