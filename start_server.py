#!/usr/bin/env python3
"""
Development Server Startup
Starts FastAPI server with query endpoints for UI integration testing
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc_clean.plugins.api.api_server import QCAPIServer
from qc_clean.core.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start_development_server():
    """Start server for UI integration testing"""
    
    logger.info("Starting Qualitative Coding Server for UI Integration")
    logger.info("=" * 60)
    
    server_config = {
        'enable_docs': config.enable_docs,
        'cors_origins': config.cors_origins,
        'background_processing_enabled': config.background_processing_enabled
    }
    
    server = QCAPIServer(server_config)
    
    logger.info("Server configuration:")
    logger.info(f"  CORS Origins: {server_config['cors_origins']}")
    logger.info(f"  API Docs: {'Enabled' if server_config['enable_docs'] else 'Disabled'}")
    logger.info(f"  Background Processing: {'Enabled' if server_config['background_processing_enabled'] else 'Disabled'}")
    
    # Start server with HTTP binding
    logger.info(f"Attempting to start HTTP server on {config.server_host}:{config.server_port}...")
    
    try:
        success = await server.start_server(host=config.server_host, port=config.server_port)
        
        if success:
            base_url = f"http://{config.server_host}:{config.server_port}"
            logger.info("✅ Server started successfully!")
            logger.info("📡 Server endpoints:")
            logger.info(f"  Health Check: {base_url}/health")
            logger.info(f"  Query Endpoint: {base_url}/api/query/natural-language")
            logger.info(f"  API Documentation: {base_url}/docs")
            logger.info("")
            logger.info("🌐 UI Access:")
            logger.info("  Direct File: Open UI_planning/mockups/02_project_workspace.html")
            logger.info(f"  Server Served: {base_url}/ui/02_project_workspace.html (if static files enabled)")
            logger.info("")
            logger.info("Press Ctrl+C to stop the server")
            
            # Keep server running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Received shutdown signal")
                logger.info("Stopping server...")
                server.stop_server()
                logger.info("Server stopped successfully")
        else:
            logger.error("❌ Failed to start server")
            logger.error("Check the logs above for specific error details")
            return False
            
    except Exception as e:
        logger.error(f"❌ Server startup failed with exception: {e}")
        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        return False
    
    return True

def check_dependencies():
    """Check if required dependencies are available"""
    logger.info("Checking dependencies...")
    
    try:
        import fastapi
        logger.info(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError:
        logger.error("❌ FastAPI not available. Install with: pip install fastapi")
        return False
        
    try:
        import uvicorn
        logger.info(f"✅ Uvicorn: {uvicorn.__version__}")
    except ImportError:
        logger.error("❌ Uvicorn not available. Install with: pip install uvicorn")
        return False
    
    logger.info("All dependencies verified")
    
    try:
        from qc_clean.core.llm.llm_handler import LLMHandler
        logger.info("✅ LLM Handler: Available")
    except ImportError as e:
        logger.warning(f"⚠️  LLM Handler: {e}")
        logger.warning("Query processing may not work correctly")
        
    return True

if __name__ == "__main__":
    logger.info("Qualitative Coding Development Server")
    logger.info("====================================")
    
    # Check dependencies first
    if not check_dependencies():
        logger.error("❌ Dependency check failed. Please install missing packages.")
        sys.exit(1)
    
    # Start server
    try:
        success = asyncio.run(start_development_server())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Server startup interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)