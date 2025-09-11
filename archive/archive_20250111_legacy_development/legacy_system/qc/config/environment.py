"""
Production environment configuration with security best practices.
"""
import os
from enum import Enum
from typing import List, Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import field_validator
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings
    from pydantic import validator as field_validator


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ProductionConfig(BaseSettings):
    """Production configuration with security validation."""
    
    # Environment
    environment: Environment = Environment.DEVELOPMENT
    
    # Database Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str
    
    # LLM API Configuration
    gemini_api_key: str
    
    # Security Configuration
    secret_key: str = os.urandom(32).hex()
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    
    # Monitoring Configuration
    log_level: str = "INFO"
    enable_metrics: bool = True
    enable_health_checks: bool = True
    
    # Performance Configuration
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 300
    database_pool_size: int = 10
    
    @field_validator('gemini_api_key')
    def validate_api_key(cls, v):
        if not v or len(v) < 20:
            raise ValueError("Invalid Gemini API key format")
        return v
    
    @field_validator('neo4j_password')
    def validate_neo4j_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError("Neo4j password must be at least 8 characters")
        return v
    
    @field_validator('secret_key')
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        return v
    
    @field_validator('allowed_hosts')
    def validate_allowed_hosts(cls, v):
        if not v:
            raise ValueError("At least one allowed host must be specified")
        return v
    
    class Config:
        env_file = ".env.production"
        case_sensitive = False


def get_config() -> ProductionConfig:
    """Get production configuration with environment variables."""
    return ProductionConfig()


def is_production() -> bool:
    """Check if running in production environment."""
    return get_config().environment == Environment.PRODUCTION


def is_development() -> bool:
    """Check if running in development environment."""
    return get_config().environment == Environment.DEVELOPMENT