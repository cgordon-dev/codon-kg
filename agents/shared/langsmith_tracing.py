"""
LangSmith Tracing Integration

Provides simple integration with LangSmith for tracking agent actions and reasoning.
"""

import os
from typing import Optional, Dict, Any
import structlog
from functools import wraps

from config.settings import LangSmithConfig

logger = structlog.get_logger(__name__)

def setup_langsmith(config: LangSmithConfig) -> bool:
    """
    Setup LangSmith tracing with the provided configuration.
    
    Args:
        config: LangSmith configuration
        
    Returns:
        bool: True if setup successful, False otherwise
    """
    if not config.enabled:
        logger.info("LangSmith tracing is disabled")
        return False
    
    if not config.api_key:
        logger.warning("LangSmith enabled but no API key provided")
        return False
    
    try:
        # Set environment variables for LangSmith
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = config.api_key
        os.environ["LANGCHAIN_PROJECT"] = config.project
        os.environ["LANGCHAIN_ENDPOINT"] = config.endpoint
        
        # Set session name if provided
        if config.session_name:
            os.environ["LANGCHAIN_SESSION"] = config.session_name
        
        logger.info("LangSmith tracing configured", 
                   project=config.project, 
                   endpoint=config.endpoint,
                   session=config.session_name)
        
        # Test the connection
        try:
            from langsmith import Client
            client = Client(api_key=config.api_key, api_url=config.endpoint)
            # Simple test to verify connection
            client.list_runs(limit=1)
            logger.info("LangSmith connection verified successfully")
            return True
            
        except Exception as e:
            logger.warning("LangSmith connection test failed", error=str(e))
            # Don't fail if connection test fails - tracing might still work
            return True
            
    except Exception as e:
        logger.error("Failed to setup LangSmith tracing", error=str(e))
        return False

def with_langsmith_session(session_name: str):
    """
    Decorator to wrap function calls with a specific LangSmith session.
    
    Args:
        session_name: Name for the LangSmith session
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Store original session
            original_session = os.environ.get("LANGCHAIN_SESSION")
            
            try:
                # Set session for this call
                os.environ["LANGCHAIN_SESSION"] = session_name
                return func(*args, **kwargs)
            finally:
                # Restore original session
                if original_session:
                    os.environ["LANGCHAIN_SESSION"] = original_session
                elif "LANGCHAIN_SESSION" in os.environ:
                    del os.environ["LANGCHAIN_SESSION"]
        
        return wrapper
    return decorator

def create_langsmith_tags(agent_name: str, query_type: str, additional_tags: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Create standardized tags for LangSmith tracing.
    
    Args:
        agent_name: Name of the agent (prometheus, neo4j, infrastructure)
        query_type: Type of query or operation
        additional_tags: Additional custom tags
        
    Returns:
        Dict[str, str]: Tags dictionary for LangSmith
    """
    tags = {
        "agent": agent_name,
        "query_type": query_type,
        "system": "codon-kg"
    }
    
    if additional_tags:
        # Convert all values to strings for LangSmith compatibility
        tags.update({k: str(v) for k, v in additional_tags.items()})
    
    return tags

def create_langsmith_metadata(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create standardized metadata for LangSmith tracing.
    
    Args:
        context: Additional context information
        
    Returns:
        Dict[str, Any]: Metadata dictionary for LangSmith
    """
    metadata = {
        "system": "codon-kg-agents",
        "version": "1.0.0"
    }
    
    if context:
        metadata.update(context)
    
    return metadata

class LangSmithTracer:
    """Simple wrapper for LangSmith tracing operations."""
    
    def __init__(self, config: LangSmithConfig):
        self.config = config
        self.enabled = setup_langsmith(config)
    
    def is_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled and working."""
        return self.enabled and self.config.enabled
    
    def set_session(self, session_name: str):
        """Set the current LangSmith session."""
        if self.enabled:
            os.environ["LANGCHAIN_SESSION"] = session_name
            logger.debug("LangSmith session set", session=session_name)
    
    def clear_session(self):
        """Clear the current LangSmith session."""
        if "LANGCHAIN_SESSION" in os.environ:
            del os.environ["LANGCHAIN_SESSION"]
            logger.debug("LangSmith session cleared")
    
    def add_tags(self, **tags):
        """Add tags to the current trace context."""
        if self.enabled:
            try:
                from langchain_core.tracers.context import collect_runs
                # This is a simplified approach - in practice, you'd want to 
                # add tags to specific run contexts
                logger.debug("Adding LangSmith tags", tags=tags)
            except ImportError:
                logger.warning("LangChain tracing context not available")
    
    def get_trace_url(self, run_id: str) -> Optional[str]:
        """Get the LangSmith trace URL for a specific run."""
        if self.enabled and run_id:
            return f"{self.config.endpoint}/o/projects/{self.config.project}/r/{run_id}"
        return None

# Global tracer instance (initialized by agent factory)
_global_tracer: Optional[LangSmithTracer] = None

def get_tracer() -> Optional[LangSmithTracer]:
    """Get the global LangSmith tracer instance."""
    return _global_tracer

def set_tracer(tracer: LangSmithTracer):
    """Set the global LangSmith tracer instance."""
    global _global_tracer
    _global_tracer = tracer