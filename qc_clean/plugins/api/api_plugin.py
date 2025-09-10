#!/usr/bin/env python3
"""
API Server Plugin Implementation

This plugin provides REST API and WebSocket functionality 
as an optional extension to the core GT workflow.
"""

import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from plugins.base import APIPlugin, PluginStatus
from .api_server import QCAPIServer

logger = logging.getLogger(__name__)


class APIServerPlugin(APIPlugin):
    """API Server Plugin Implementation"""
    
    def __init__(self):
        super().__init__()
        self.api_server: Optional[QCAPIServer] = None
        self.server_config: Optional[Dict[str, Any]] = None
        self.gt_workflow = None
        self._logger = logging.getLogger(f"{__name__}.APIServerPlugin")
        self._server_task: Optional[asyncio.Task] = None
    
    def get_name(self) -> str:
        """Return plugin name"""
        return "api_server"
    
    def get_version(self) -> str:
        """Return plugin version"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return plugin description"""
        return "REST API and WebSocket server for GT analysis workflows"
    
    def get_dependencies(self) -> List[str]:
        """Return plugin dependencies"""
        return ["core.cli.robust_cli_operations"]
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize API server plugin with configuration"""
        try:
            self._logger.info("Initializing API Server plugin...")
            
            # Store configuration
            self._config = config
            self.server_config = {
                'host': config.get('host', 'localhost'),
                'port': config.get('port', 8000),
                'auto_start': config.get('auto_start', False),
                'enable_background_processing': config.get('enable_background_processing', True),
                'cors_origins': config.get('cors_origins', ["*"]),
                'enable_docs': config.get('enable_docs', True)
            }
            
            # Initialize API server
            self.api_server = QCAPIServer(self.server_config)
            
            self.status = PluginStatus.INITIALIZED
            self._logger.info("API Server plugin initialized successfully")
            
            # Auto-start if configured
            if self.server_config.get('auto_start', False):
                return self.start_server()
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to initialize API server plugin: {e}")
            self.status = PluginStatus.ERROR
            return False
    
    def is_available(self) -> bool:
        """Check if API server plugin dependencies are available"""
        try:
            # Check for FastAPI and related dependencies
            import fastapi
            import uvicorn
            
            # Check for WebSocket support
            import websockets
            
            # Check for async support
            import asyncio
            
            return True
            
        except ImportError as e:
            self._logger.error(f"Required API dependencies not available: {e}")
            return False
    
    def start_server(self, host: str = None, port: int = None) -> bool:
        """Start API server"""
        if not self.api_server:
            self._logger.error("API server not initialized")
            return False
        
        try:
            # Use provided host/port or fall back to config
            server_host = host or self.server_config.get('host', 'localhost')
            server_port = port or self.server_config.get('port', 8000)
            
            self._logger.info(f"Starting API server on {server_host}:{server_port}...")
            
            # Start server in background task
            loop = asyncio.get_event_loop()
            self._server_task = loop.create_task(
                self.api_server.start_server(server_host, server_port)
            )
            
            self.status = PluginStatus.ACTIVE
            self._logger.info(f"API server started successfully on {server_host}:{server_port}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to start API server: {e}")
            self.status = PluginStatus.ERROR
            return False
    
    def stop_server(self) -> bool:
        """Stop API server"""
        if not self.api_server:
            return True
        
        try:
            self._logger.info("Stopping API server...")
            
            # Cancel server task if running
            if self._server_task and not self._server_task.done():
                self._server_task.cancel()
            
            # Stop the server
            success = self.api_server.stop_server()
            
            if success:
                self.status = PluginStatus.INITIALIZED
                self._logger.info("API server stopped successfully")
            else:
                self._logger.warning("API server stop returned false")
                
            return success
            
        except Exception as e:
            self._logger.error(f"Error stopping API server: {e}")
            return False
    
    def register_gt_endpoints(self, gt_workflow) -> None:
        """Register GT analysis endpoints"""
        if not self.api_server:
            self._logger.error("API server not initialized")
            return
        
        try:
            self._logger.info("Registering GT workflow endpoints...")
            
            # Store reference to GT workflow
            self.gt_workflow = gt_workflow
            
            # Register endpoints with the API server
            self.api_server.register_gt_workflow(gt_workflow)
            
            self._logger.info("GT workflow endpoints registered successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to register GT endpoints: {e}")
    
    def enable_background_processing(self) -> bool:
        """Enable background task processing"""
        if not self.api_server:
            self._logger.error("API server not initialized")
            return False
        
        try:
            self._logger.info("Enabling background processing...")
            
            # Enable background processing in the API server
            success = self.api_server.enable_background_processing()
            
            if success:
                self._logger.info("Background processing enabled successfully")
            else:
                self._logger.warning("Background processing enable returned false")
                
            return success
            
        except Exception as e:
            self._logger.error(f"Failed to enable background processing: {e}")
            return False
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get current server status"""
        if not self.api_server:
            return {
                'initialized': False,
                'running': False,
                'host': None,
                'port': None
            }
        
        return self.api_server.get_status()
    
    def is_server_running(self) -> bool:
        """Check if server is currently running"""
        status = self.get_server_status()
        return status.get('running', False)
    
    def get_endpoint_info(self) -> List[Dict[str, Any]]:
        """Get information about registered endpoints"""
        if not self.api_server:
            return []
        
        return self.api_server.get_endpoints()
    
    def cleanup(self) -> bool:
        """Cleanup API server plugin resources"""
        try:
            self._logger.info("Cleaning up API server plugin resources...")
            
            # Stop server if running
            if self.is_server_running():
                self.stop_server()
            
            # Clean up server instance
            if self.api_server:
                self.api_server.cleanup()
                self.api_server = None
            
            # Clean up references
            self.gt_workflow = None
            self.server_config = None
            
            # Cancel any running tasks
            if self._server_task and not self._server_task.done():
                self._server_task.cancel()
            
            self.status = PluginStatus.DISABLED
            self._logger.info("API server plugin cleanup completed")
            return True
            
        except Exception as e:
            self._logger.error(f"Error during API server plugin cleanup: {e}")
            return False