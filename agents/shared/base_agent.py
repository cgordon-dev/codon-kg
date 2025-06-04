from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from pydantic import BaseModel, Field
import structlog
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

logger = structlog.get_logger(__name__)

class BaseAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    metadata: Dict[str, Any]
    context: Dict[str, Any]
    error_count: int
    max_retries: int

class AgentConfig(BaseModel):
    name: str = Field(..., description="Agent name")
    model_name: str = Field(default="claude-3-sonnet-20240229", description="LLM model")
    temperature: float = Field(default=0.1, description="Model temperature")
    max_tokens: int = Field(default=4000, description="Max tokens per response")
    timeout: int = Field(default=300, description="Timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    system_prompt: str = Field(..., description="System prompt for the agent")

class BaseAgent(ABC):
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = structlog.get_logger(self.__class__.__name__)
        self._setup_logging()
    
    def _setup_logging(self):
        self.logger = self.logger.bind(agent_name=self.config.name)
    
    @abstractmethod
    def create_tools(self) -> List[Any]:
        pass
    
    @abstractmethod
    def build_graph(self) -> Any:
        pass
    
    def get_initial_state(self) -> BaseAgentState:
        return BaseAgentState(
            messages=[],
            metadata={"agent_name": self.config.name},
            context={},
            error_count=0,
            max_retries=self.config.max_retries
        )
    
    def handle_error(self, error: Exception, state: BaseAgentState) -> BaseAgentState:
        self.logger.error("Agent error occurred", error=str(error), error_count=state["error_count"])
        state["error_count"] += 1
        return state
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        required_fields = ["messages"]
        return all(field in input_data for field in required_fields)