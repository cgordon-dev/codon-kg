"""
LLM Factory for creating model instances based on provider configuration.
"""

from typing import Any
import structlog
from langchain_core.language_models.base import BaseLanguageModel

from config.settings import LLMConfig, LangSmithConfig
from .langsmith_tracing import setup_langsmith, LangSmithTracer, set_tracer

logger = structlog.get_logger(__name__)

class LLMFactory:
    """Factory for creating LLM instances based on provider configuration."""
    
    @staticmethod
    def create_llm(config: LLMConfig, langsmith_config: LangSmithConfig = None) -> BaseLanguageModel:
        """
        Create an LLM instance based on the provider configuration.
        
        Args:
            config: LLM configuration containing provider, model, and API keys
            langsmith_config: Optional LangSmith configuration for tracing
            
        Returns:
            BaseLanguageModel: Configured LLM instance
            
        Raises:
            ValueError: If provider is not supported or API key is missing
            ImportError: If required package is not installed
        """
        # Setup LangSmith tracing if configured
        if langsmith_config:
            tracer = LangSmithTracer(langsmith_config)
            set_tracer(tracer)
            if tracer.is_enabled():
                logger.info("LangSmith tracing enabled for LLM", project=langsmith_config.project)
        
        provider = config.provider.lower()
        
        if provider == "openai":
            return LLMFactory._create_openai_llm(config)
        elif provider == "anthropic":
            return LLMFactory._create_anthropic_llm(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}. Supported providers: 'openai', 'anthropic'")
    
    @staticmethod
    def _create_openai_llm(config: LLMConfig) -> BaseLanguageModel:
        """Create OpenAI LLM instance."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai package is required for OpenAI models. "
                "Install it with: pip install langchain-openai"
            )
        
        if not config.openai_api_key:
            raise ValueError("OpenAI API key is required for OpenAI provider")
        
        logger.info("Creating OpenAI LLM", model=config.model_name, temperature=config.temperature)
        
        return ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=config.openai_api_key
        )
    
    @staticmethod
    def _create_anthropic_llm(config: LLMConfig) -> BaseLanguageModel:
        """Create Anthropic LLM instance."""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic package is required for Anthropic models. "
                "Install it with: pip install langchain-anthropic"
            )
        
        if not config.anthropic_api_key:
            raise ValueError("Anthropic API key is required for Anthropic provider")
        
        logger.info("Creating Anthropic LLM", model=config.model_name, temperature=config.temperature)
        
        return ChatAnthropic(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            anthropic_api_key=config.anthropic_api_key
        )
    
    @staticmethod
    def get_default_model_for_provider(provider: str) -> str:
        """Get the default model name for a given provider."""
        defaults = {
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-sonnet-20240229"
        }
        return defaults.get(provider.lower(), "gpt-3.5-turbo")
    
    @staticmethod
    def validate_model_for_provider(provider: str, model_name: str) -> bool:
        """Validate that a model name is appropriate for the given provider."""
        openai_models = [
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k", 
            "gpt-4", "gpt-4-turbo", "gpt-4o",
            "gpt-4-32k", "gpt-4-1106-preview"
        ]
        
        anthropic_models = [
            "claude-3-sonnet-20240229", "claude-3-opus-20240229", 
            "claude-3-haiku-20240307", "claude-2.1", "claude-2.0",
            "claude-instant-1.2"
        ]
        
        if provider.lower() == "openai":
            return model_name in openai_models or model_name.startswith("gpt-")
        elif provider.lower() == "anthropic":
            return model_name in anthropic_models or model_name.startswith("claude-")
        
        return False