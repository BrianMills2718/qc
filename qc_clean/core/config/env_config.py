"""
Server configuration loaded from environment variables.

Only contains settings needed by start_server.py / QCAPIServer.
LLM and analysis config is in qc_clean/config/unified_config.py.
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class EnvironmentConfig:
    """Server environment configuration with fallback defaults."""

    @property
    def server_host(self) -> str:
        return os.getenv("SERVER_HOST", "127.0.0.1")

    @property
    def server_port(self) -> int:
        try:
            return int(os.getenv("SERVER_PORT", "8002"))
        except ValueError:
            return 8002

    @property
    def cors_origins(self) -> List[str]:
        env_origins = os.getenv("CORS_ORIGINS", "")
        if env_origins:
            return [o.strip() for o in env_origins.split(",") if o.strip()]
        return ["*"]

    @property
    def enable_docs(self) -> bool:
        return os.getenv("ENABLE_DOCS", "true").lower() in ("true", "1", "yes", "on")

    @property
    def background_processing_enabled(self) -> bool:
        return os.getenv("BACKGROUND_PROCESSING_ENABLED", "true").lower() in ("true", "1", "yes", "on")


config = EnvironmentConfig()