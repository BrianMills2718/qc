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
    
    config = {
        'enable_docs': True,
        'cors_origins': [
            "http://localhost:8002",
            "http://127.0.0.1:8002",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "http://localhost:8000", 
            "http://127.0.0.1:8000",
            "file://",  # Allow file:// protocol for direct HTML opening
            "null"      # Allow null origin for local file testing
        ],
        'background_processing_enabled': False  # Not needed for query testing
    }
    
    server = QCAPIServer(config)
    
    logger.info("Server configuration:")
    logger.info(f"  CORS Origins: {config['cors_origins']}")
    logger.info(f"  API Docs: {'Enabled' if config['enable_docs'] else 'Disabled'}")
    logger.info(f"  Background Processing: {'Enabled' if config['background_processing_enabled'] else 'Disabled'}")
    
    # Start server with HTTP binding
    logger.info("Attempting to start HTTP server on 127.0.0.1:8002...")
    
    try:
        success = await server.start_server(host="127.0.0.1", port=8002)
        
        if success:
            logger.info("✅ Server started successfully!")
            logger.info("📡 Server endpoints:")
            logger.info("  Health Check: http://127.0.0.1:8002/health")
            logger.info("  Query Endpoint: http://127.0.0.1:8002/api/query/natural-language")
            logger.info("  API Documentation: http://127.0.0.1:8002/docs")
            logger.info("")
            logger.info("🌐 UI Access:")
            logger.info("  Direct File: Open UI_planning/mockups/02_project_workspace.html")
            logger.info("  Server Served: http://127.0.0.1:8002/ui/02_project_workspace.html (if static files enabled)")
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
    
    # Check for AI system components
    try:
        from investigation_ai_quality_assessment import AIQueryGenerationAssessment
        logger.info("✅ AI Query Generation System: Available")
    except ImportError as e:
        logger.warning(f"⚠️  AI Query Generation System: {e}")
        logger.warning("Query endpoints may use mock responses")
    
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