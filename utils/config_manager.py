#!/usr/bin/env python3
"""
Secure Configuration and Secrets Management
Handles environment variables, configuration files, and secret management
"""

import os
import warnings
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, validator, SecretStr
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings, Field, validator, SecretStr
import yaml
import json


class SecurityError(Exception):
    """Raised when security requirements are not met"""
    pass


class SecureSettings(BaseSettings):
    """Secure configuration management with validation"""
    
    # API Keys (stored as SecretStr to prevent accidental logging)
    openai_api_key: Optional[SecretStr] = Field(None, env='OPENAI_API_KEY')
    gemini_api_key: Optional[SecretStr] = Field(None, env='GEMINI_API_KEY') 
    anthropic_api_key: Optional[SecretStr] = Field(None, env='ANTHROPIC_API_KEY')
    
    # Model Configuration
    gemini_model: str = Field('gemini-2.5-flash', env='GEMINI_MODEL')
    
    # Database Configuration
    database_url: str = Field('sqlite:///qualitative_coding.db', env='DATABASE_URL')
    neo4j_uri: str = Field('bolt://localhost:7687', env='NEO4J_URI')
    neo4j_username: str = Field('neo4j', env='NEO4J_USERNAME')
    neo4j_password: Optional[SecretStr] = Field(None, env='NEO4J_PASSWORD')
    neo4j_enabled: bool = Field(False, env='NEO4J_ENABLED')
    
    # Security Settings
    secret_key: Optional[SecretStr] = Field(None, env='SECRET_KEY')
    allowed_hosts: List[str] = Field(['localhost', '127.0.0.1'], env='ALLOWED_HOSTS')
    cors_origins: List[str] = Field(['http://localhost:3000'], env='CORS_ORIGINS')
    max_file_size_mb: int = Field(10, env='MAX_FILE_SIZE_MB')
    rate_limit_per_minute: int = Field(60, env='RATE_LIMIT_PER_MINUTE')
    
    # Application Settings
    environment: str = Field('development', env='ENVIRONMENT')
    debug: bool = Field(False, env='DEBUG')
    log_level: str = Field('INFO', env='LOG_LEVEL')
    
    # Performance Settings
    max_workers: int = Field(4, env='MAX_WORKERS')
    timeout_seconds: int = Field(30, env='TIMEOUT_SECONDS')
    max_retries: int = Field(3, env='MAX_RETRIES')
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = 'ignore'  # Ignore extra fields from env
        
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f'Environment must be one of {valid_envs}')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    @validator('max_file_size_mb')
    def validate_file_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('File size must be between 1MB and 100MB')
        return v
    
    def get_secret(self, key: str) -> Optional[str]:
        """Safely get secret value"""
        secret = getattr(self, key, None)
        if isinstance(secret, SecretStr):
            return secret.get_secret_value()
        return secret
    
    def validate_security_requirements(self) -> List[str]:
        """Validate security requirements and return warnings"""
        warnings = []
        
        # Check for required secrets in production
        if self.environment == 'production':
            if not self.secret_key:
                warnings.append("SECRET_KEY is required in production")
            if not self.gemini_api_key:
                warnings.append("GEMINI_API_KEY is required")
        
        # Check secret key strength
        if self.secret_key:
            secret_value = self.secret_key.get_secret_value()
            if len(secret_value) < 32:
                warnings.append("SECRET_KEY should be at least 32 characters long")
        
        # Check CORS configuration
        if self.environment == 'production' and 'http://localhost:3000' in self.cors_origins:
            warnings.append("Remove localhost from CORS origins in production")
        
        # Check debug mode
        if self.environment == 'production' and self.debug:
            warnings.append("Debug mode should be disabled in production")
        
        return warnings
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration with available keys"""
        config = {
            'model': self.gemini_model,
            'timeout': self.timeout_seconds,
            'max_retries': self.max_retries,
            'has_gemini_key': bool(self.gemini_api_key)
        }
            
        return config


@dataclass
class ConfigurationManager:
    """Manages configuration loading and validation"""
    
    settings: SecureSettings = field(default_factory=SecureSettings)
    _config_file: Optional[Path] = None
    
    @classmethod
    def load(cls, config_file: Optional[str] = None) -> 'ConfigurationManager':
        """Load configuration from environment and optional config file"""
        instance = cls()
        
        if config_file:
            instance._load_config_file(config_file)
        
        # Load from environment
        instance.settings = SecureSettings()
        
        # Validate security requirements
        warnings = instance.settings.validate_security_requirements()
        if warnings:
            for warning in warnings:
                print(f"⚠️  Security Warning: {warning}")
        
        return instance
    
    def _load_config_file(self, config_file: str):
        """Load additional configuration from YAML or JSON file"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_path.suffix}")
            
            # Set environment variables from config file (lower precedence than actual env vars)
            for key, value in config_data.items():
                if isinstance(value, (str, int, bool, float)):
                    env_key = key.upper()
                    if env_key not in os.environ:
                        os.environ[env_key] = str(value)
        
        except Exception as e:
            raise ValueError(f"Error loading config file {config_file}: {e}")
    
    def get_database_url(self) -> str:
        """Get database URL with proper formatting"""
        return self.settings.database_url
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        """Get Neo4j configuration"""
        return {
            'uri': self.settings.neo4j_uri,
            'username': self.settings.neo4j_username,
            'password': self.settings.get_secret('neo4j_password'),
            'enabled': self.settings.neo4j_enabled
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.settings.environment == 'production'
    
    def validate_for_deployment(self) -> bool:
        """Validate configuration for deployment"""
        warnings = self.settings.validate_security_requirements()
        
        if self.is_production():
            # Additional production checks
            if not self.settings.get_secret('secret_key'):
                raise SecurityError("SECRET_KEY is required for production deployment")
            
            if self.settings.debug:
                raise SecurityError("Debug mode must be disabled in production")
            
            if not self.settings.get_secret('gemini_api_key'):
                raise SecurityError("GEMINI_API_KEY is required")
        
        if warnings:
            print(f"⚠️  Configuration warnings found:")
            for warning in warnings:
                print(f"   • {warning}")
            return False
        
        return True


# Global configuration instance
_config_manager: Optional[ConfigurationManager] = None


def get_config() -> ConfigurationManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager.load()
    return _config_manager


def init_config(config_file: Optional[str] = None) -> ConfigurationManager:
    """Initialize configuration with optional config file"""
    global _config_manager
    _config_manager = ConfigurationManager.load(config_file)
    return _config_manager


def get_secret(key: str) -> Optional[str]:
    """Safely get a secret value"""
    return get_config().settings.get_secret(key)


def is_production() -> bool:
    """Check if running in production"""
    return get_config().is_production()


# Security utilities
def mask_secret(value: str, visible_chars: int = 4) -> str:
    """Mask a secret string showing only last few characters"""
    if not value or len(value) <= visible_chars:
        return '*' * 8
    return '*' * (len(value) - visible_chars) + value[-visible_chars:]


def validate_api_key_format(key: str, provider: str) -> bool:
    """Validate API key format for known providers"""
    if not key:
        return False
    
    patterns = {
        'openai': key.startswith('sk-'),
        'anthropic': key.startswith('sk-ant-'),
        'gemini': len(key) == 39 and key.startswith('AIza'),
    }
    
    return patterns.get(provider, True)  # Default to valid for unknown providers


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = ConfigurationManager.load()
        print("✅ Configuration loaded successfully")
        print(f"Environment: {config.settings.environment}")
        print(f"Debug mode: {config.settings.debug}")
        print(f"Gemini key configured: {config.settings.get_llm_config()['has_gemini_key']}")
        
        # Test validation
        if config.validate_for_deployment():
            print("✅ Configuration is valid for deployment")
        else:
            print("⚠️  Configuration has warnings")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")