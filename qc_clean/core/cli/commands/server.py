"""
Server Command Handler - Server management functionality
"""

import logging
import subprocess
import sys
import time
import signal
import os
from pathlib import Path
from typing import Optional, Dict, Any
from ..api_client import APIClient, APIClientError

logger = logging.getLogger(__name__)


def handle_server_command(args) -> int:
    """Handle the server command"""
    
    try:
        if args.start:
            return handle_server_start()
        elif args.stop:
            return handle_server_stop()
        elif args.status:
            return handle_server_status_check(args.api_url)
        else:
            logger.error("No server action specified")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error in server command: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
        return 1


def handle_server_start() -> int:
    """Handle server start command"""
    
    print("🚀 Starting API server...")
    
    # Find the start_server.py script
    project_root = Path.cwd()
    start_script = project_root / "start_server.py"
    
    if not start_script.exists():
        print("❌ start_server.py not found in current directory")
        print("Please run this command from the project root directory")
        return 1
    
    # Check if server is already running
    api_client = APIClient()
    if api_client.health_check():
        print("⚠️  Server appears to be already running")
        print(f"🌐 URL: {api_client.base_url}")
        
        response = input("Do you want to continue anyway? [y/N]: ")
        if response.lower() != 'y':
            return 0
    
    print(f"📄 Starting server using: {start_script}")
    
    try:
        # Start server process
        if os.name == 'nt':  # Windows
            # Use creationflags to create new process group
            process = subprocess.Popen(
                [sys.executable, str(start_script)],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:  # Unix/Linux/Mac
            process = subprocess.Popen(
                [sys.executable, str(start_script)],
                preexec_fn=os.setsid
            )
        
        print(f"🆔 Server process started with PID: {process.pid}")
        
        # Wait a moment for server to start
        print("⏳ Waiting for server to start...")
        
        # Check if server becomes available
        for i in range(10):  # Wait up to 10 seconds
            time.sleep(1)
            if api_client.health_check():
                print("✅ Server started successfully!")
                print(f"🌐 Server URL: {api_client.base_url}")
                print(f"📄 API Documentation: {api_client.base_url}/docs")
                print()
                print("To stop the server, use:")
                print("  qc_cli server --stop")
                print("  or press Ctrl+C in the server terminal")
                return 0
        
        # Check if process is still running
        if process.poll() is None:
            print("⚠️  Server process is running but not responding to health checks")
            print("This might be normal if the server takes longer to initialize")
            print(f"🆔 Process PID: {process.pid}")
            return 0
        else:
            print("❌ Server process exited unexpectedly")
            return 1
            
    except FileNotFoundError:
        print("❌ Python interpreter not found")
        print("Please ensure Python is installed and in your PATH")
        return 1
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return 1


def handle_server_stop() -> int:
    """Handle server stop command"""
    
    print("🛑 Stopping API server...")
    
    # Check if server is running
    api_client = APIClient()
    if not api_client.health_check():
        print("ℹ️  Server doesn't appear to be running")
        return 0
    
    print("⚠️  Server management through CLI is limited")
    print("To stop the server:")
    print("  1. Find the terminal where you started the server")
    print("  2. Press Ctrl+C to stop it gracefully")
    print()
    print("Alternative methods:")
    print("  • Close the terminal window running the server")
    print("  • Use task manager/process manager to kill the process")
    
    # On Unix systems, we could try to find and kill the process
    if os.name != 'nt':
        print("  • Use: pkill -f start_server.py")
    
    return 0


def handle_server_status_check(api_url: str) -> int:
    """Handle server status check"""
    
    api_client = APIClient(base_url=api_url)
    
    print("🔍 Checking server status...")
    
    if api_client.health_check():
        print("✅ Server is running and healthy")
        print(f"🌐 URL: {api_client.base_url}")
        
        # Get additional server information
        try:
            server_info = api_client.get_server_info()
            
            if 'available_endpoints' in server_info:
                print()
                print("📡 Available Endpoints:")
                for endpoint in server_info['available_endpoints']:
                    print(f"   • {endpoint}")
            
            return 0
            
        except APIClientError as e:
            logger.debug(f"Could not get additional server info: {e}")
            return 0
    
    else:
        print("❌ Server is not running or not accessible")
        print(f"🌐 Attempted URL: {api_client.base_url}")
        print()
        print("To start the server:")
        print("  qc_cli server --start")
        print("  or manually: python start_server.py")
        return 1


def find_server_process() -> Optional[int]:
    """Try to find the server process PID (Unix only)"""
    
    if os.name == 'nt':
        return None
    
    try:
        # Try to find process by name
        result = subprocess.run(
            ['pgrep', '-f', 'start_server.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip().split('\n')[0])
            
    except (subprocess.SubprocessError, ValueError, FileNotFoundError):
        pass
    
    return None