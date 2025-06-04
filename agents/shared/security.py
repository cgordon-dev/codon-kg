import os
import hashlib
import hmac
from typing import Dict, Any, Optional
from functools import wraps
import structlog

logger = structlog.get_logger(__name__)

class SecurityManager:
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv("AGENT_SECRET_KEY", "default-secret")
        self.allowed_actions = set()
        self.blocked_patterns = [
            "rm -rf",
            "DELETE FROM",
            "DROP TABLE",
            "shutdown",
            "reboot"
        ]
    
    def add_allowed_action(self, action: str):
        self.allowed_actions.add(action)
    
    def validate_command(self, command: str) -> bool:
        for pattern in self.blocked_patterns:
            if pattern.lower() in command.lower():
                logger.warning("Blocked potentially dangerous command", command=command, pattern=pattern)
                return False
        return True
    
    def sanitize_input(self, input_data: str) -> str:
        dangerous_chars = ["<", ">", "&", "|", ";", "`", "$", "(", ")"]
        sanitized = input_data
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        return sanitized
    
    def generate_audit_hash(self, data: Dict[str, Any]) -> str:
        serialized = str(sorted(data.items()))
        return hmac.new(
            self.secret_key.encode(),
            serialized.encode(),
            hashlib.sha256
        ).hexdigest()

def require_security_check(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        security_manager = SecurityManager()
        if "command" in kwargs:
            if not security_manager.validate_command(kwargs["command"]):
                raise PermissionError("Command blocked by security policy")
        return func(*args, **kwargs)
    return wrapper

def audit_log(action: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info("Agent action started", action=action, function=func.__name__)
            try:
                result = func(*args, **kwargs)
                logger.info("Agent action completed", action=action, function=func.__name__)
                return result
            except Exception as e:
                logger.error("Agent action failed", action=action, function=func.__name__, error=str(e))
                raise
        return wrapper
    return decorator