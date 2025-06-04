import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import yaml
import structlog

load_dotenv()
logger = structlog.get_logger(__name__)

class DatabaseConfig(BaseModel):
    neo4j_uri: str = Field(default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    neo4j_username: str = Field(default=os.getenv("NEO4J_USERNAME", "neo4j"))
    neo4j_password: str = Field(default=os.getenv("NEO4J_PASSWORD", "password"))
    neo4j_database: str = Field(default=os.getenv("NEO4J_DATABASE", "neo4j"))

class MonitoringConfig(BaseModel):
    prometheus_url: str = Field(default=os.getenv("PROMETHEUS_URL", "http://localhost:9090"))
    prometheus_auth_token: Optional[str] = Field(default=os.getenv("PROMETHEUS_AUTH_TOKEN"))
    alert_webhook_url: Optional[str] = Field(default=os.getenv("ALERT_WEBHOOK_URL"))

class CloudConfig(BaseModel):
    aws_region: str = Field(default=os.getenv("AWS_REGION", "us-east-1"))
    aws_profile: Optional[str] = Field(default=os.getenv("AWS_PROFILE"))
    aws_access_key_id: Optional[str] = Field(default=os.getenv("AWS_ACCESS_KEY_ID"))
    aws_secret_access_key: Optional[str] = Field(default=os.getenv("AWS_SECRET_ACCESS_KEY"))
    terraform_dir: str = Field(default=os.getenv("TERRAFORM_DIR", "./terraform"))

class LLMConfig(BaseModel):
    model_name: str = Field(default=os.getenv("LLM_MODEL", "claude-3-sonnet-20240229"))
    temperature: float = Field(default=float(os.getenv("LLM_TEMPERATURE", "0.1")))
    max_tokens: int = Field(default=int(os.getenv("LLM_MAX_TOKENS", "4000")))
    anthropic_api_key: Optional[str] = Field(default=os.getenv("ANTHROPIC_API_KEY"))

class SecurityConfig(BaseModel):
    secret_key: str = Field(default=os.getenv("AGENT_SECRET_KEY", "default-secret-key"))
    enable_audit_logging: bool = Field(default=os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true")
    max_retry_attempts: int = Field(default=int(os.getenv("MAX_RETRY_ATTEMPTS", "3")))
    command_timeout: int = Field(default=int(os.getenv("COMMAND_TIMEOUT", "300")))

class GlobalConfig(BaseModel):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    cloud: CloudConfig = Field(default_factory=CloudConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "GlobalConfig":
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                config_data = yaml.safe_load(file)
            
            return cls(**config_data)
        except FileNotFoundError:
            logger.warning("Config file not found, using default values", path=config_path)
            return cls()
        except yaml.YAMLError as e:
            logger.error("Failed to parse YAML config", error=str(e), path=config_path)
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()
    
    def validate_configuration(self) -> Dict[str, str]:
        """Validate configuration and return any issues."""
        issues = []
        
        # Check required API keys
        if not self.llm.anthropic_api_key:
            issues.append("ANTHROPIC_API_KEY is not set")
        
        # Check database connectivity requirements
        if not all([self.database.neo4j_uri, self.database.neo4j_username, self.database.neo4j_password]):
            issues.append("Neo4j database configuration is incomplete")
        
        # Check monitoring configuration
        if not self.monitoring.prometheus_url:
            issues.append("Prometheus URL is not configured")
        
        # Check Terraform directory
        if not os.path.exists(self.cloud.terraform_dir):
            issues.append(f"Terraform directory does not exist: {self.cloud.terraform_dir}")
        
        return {"status": "valid" if not issues else "invalid", "issues": issues}

# Global configuration instance
config = GlobalConfig()

def get_config() -> GlobalConfig:
    """Get the global configuration instance."""
    return config

def reload_config(config_path: Optional[str] = None) -> GlobalConfig:
    """Reload configuration from file or environment."""
    global config
    
    if config_path:
        config = GlobalConfig.from_yaml(config_path)
    else:
        config = GlobalConfig()
    
    validation_result = config.validate_configuration()
    if validation_result["status"] == "invalid":
        logger.warning("Configuration validation failed", issues=validation_result["issues"])
    else:
        logger.info("Configuration loaded successfully")
    
    return config