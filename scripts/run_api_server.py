#!/usr/bin/env python3
"""
API Server startup script for Qualitative Coding Analysis Tool.
"""
import os
import sys
import logging
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Start the FastAPI server."""
    try:
        import uvicorn
        from qc.api.main import app
        
        # Get configuration from environment
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", "8000"))
        workers = int(os.getenv("API_WORKERS", "1"))
        reload = os.getenv("API_RELOAD", "false").lower() == "true"
        log_level = os.getenv("LOG_LEVEL", "info").lower()
        
        logger.info(f"Starting API server on {host}:{port}")
        logger.info(f"Workers: {workers}, Reload: {reload}, Log Level: {log_level}")
        
        # Run the server
        uvicorn.run(
            "src.qc.api.main:app",
            host=host,
            port=port,
            workers=workers if not reload else 1,  # Single worker for reload mode
            reload=reload,
            log_level=log_level,
            access_log=True
        )
        
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Install FastAPI dependencies: pip install fastapi uvicorn")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()