"""
Environment Configuration Module
Loads configuration from environment variables with fallback defaults
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load .env file if present (silently fail if not)
load_dotenv()


class EnvironmentConfig:
    """Environment configuration with fallback defaults"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        pass
    
    @property
    def neo4j_uri(self) -> str:
        """Neo4j database URI"""
        return os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    
    @property
    def neo4j_username(self) -> str:
        """Neo4j database username"""
        return os.getenv('NEO4J_USERNAME', 'neo4j')
    
    @property 
    def neo4j_password(self) -> str:
        """Neo4j database password"""
        return os.getenv('NEO4J_PASSWORD', 'password')
    
    @property
    def server_host(self) -> str:
        """Server host address"""
        return os.getenv('SERVER_HOST', '127.0.0.1')
    
    @property
    def server_port(self) -> int:
        """Server port number"""
        try:
            return int(os.getenv('SERVER_PORT', '8002'))
        except ValueError:
            return 8002
    
    @property
    def cors_origins(self) -> List[str]:
        """CORS allowed origins"""
        # Allow comma-separated list in environment variable
        env_origins = os.getenv('CORS_ORIGINS', '')
        if env_origins:
            return [origin.strip() for origin in env_origins.split(',') if origin.strip()]
        
        # Default origins
        return [
            "http://localhost:3000",   # React frontend
            "http://127.0.0.1:3000",  # React frontend
            "http://localhost:8002",
            "http://127.0.0.1:8002", 
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "file://",
            "null"
        ]
    
    @property
    def llm_model_name(self) -> str:
        """LLM model name"""
        return os.getenv('LLM_MODEL_NAME', 'gpt-4o-mini')
    
    @property
    def enable_docs(self) -> bool:
        """Enable API documentation"""
        return os.getenv('ENABLE_DOCS', 'true').lower() in ('true', '1', 'yes', 'on')
    
    @property
    def background_processing_enabled(self) -> bool:
        """Enable background task processing"""
        return os.getenv('BACKGROUND_PROCESSING_ENABLED', 'true').lower() in ('true', '1', 'yes', 'on')


# Global configuration instance
config = EnvironmentConfig()