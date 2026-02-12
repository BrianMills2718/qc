"""
Status Command Handler - System status monitoring
"""

import logging
from typing import Dict, Any
from ..api_client import APIClient, APIClientError
from ..formatters.human_formatter import format_status_info
from ..formatters.json_formatter import format_json_output

logger = logging.getLogger(__name__)


def handle_status_command(args) -> int:
    """Handle the status command"""
    
    try:
        # Initialize API client
        api_client = APIClient(base_url=args.api_url)
        
        if args.job:
            return handle_job_status(api_client, args.job)
        elif args.server:
            return handle_server_status(api_client)
        else:
            return handle_overall_status(api_client)
            
    except Exception as e:
        logger.error(f"Unexpected error in status command: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
        return 1


def handle_overall_status(api_client: APIClient) -> int:
    """Handle overall system status check"""
    
    print("Checking system status...")
    print()
    
    status_data = {}
    
    # Check server connectivity
    server_running = api_client.health_check()
    status_data['server_status'] = 'running' if server_running else 'not_running'
    
    if server_running:
        print("[OK] API Server: Running")
        
        # Get server information
        try:
            server_info = api_client.get_server_info()
            status_data.update(server_info)
            
            # Show available endpoints
            endpoints = server_info.get('available_endpoints', [])
            if endpoints:
                print("Available Endpoints:")
                for endpoint in endpoints:
                    print(f"   - {endpoint}")
        except APIClientError as e:
            logger.debug(f"Could not get server info: {e}")
        
        print()
        print("Server URL:", api_client.base_url)
        
    else:
        print("[ERROR] API Server: Not Running")
        print()
        print("To start the server, run:")
        print("  python start_server.py")
    
    print()
    
    # Check additional system components
    print("🔧 System Components:")
    
    # Check if required directories exist
    from pathlib import Path
    project_root = Path.cwd()
    
    required_paths = [
        ('qc_clean', 'Core system'),
        ('qc_clean/plugins/api', 'API plugin'),
        ('qc_clean/core/data', 'Data layer'),
        ('.env', 'Configuration file')
    ]
    
    for path, description in required_paths:
        path_obj = project_root / path
        if path_obj.exists():
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} (missing: {path})")
    
    print()
    
    # Overall system health
    if server_running:
        print("🎯 Overall Status: ✅ HEALTHY")
        return 0
    else:
        print("🎯 Overall Status: ⚠️  SERVER NOT RUNNING")
        return 1


def handle_server_status(api_client: APIClient) -> int:
    """Handle server-only status check"""
    
    print("🔍 Checking server connectivity...")
    
    server_running = api_client.health_check()
    
    if server_running:
        print("✅ Server is running and responsive")
        print(f"🌐 URL: {api_client.base_url}")
        
        # Test endpoints
        print()
        print("📡 Testing endpoints...")
        
        endpoints_to_test = [
            ('/health', 'Health check'),
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                response = api_client.session.get(f"{api_client.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {description}: OK")
                else:
                    print(f"   ⚠️  {description}: Status {response.status_code}")
            except Exception as e:
                print(f"   ❌ {description}: Failed ({e})")
        
        return 0
    else:
        print("❌ Server is not running or not accessible")
        print(f"🌐 Attempted URL: {api_client.base_url}")
        print()
        print("To start the server, run:")
        print("  python start_server.py")
        return 1


def handle_job_status(api_client: APIClient, job_id: str) -> int:
    """Handle specific job status check"""
    
    print(f"🔍 Checking status for job: {job_id}")
    
    # Check server connectivity first
    if not api_client.health_check():
        print("❌ Cannot connect to API server.")
        print("Please start the server with: python start_server.py")
        return 1
    
    print("✅ Connected to API server")
    
    try:
        job_data = api_client.get_job_status(job_id)
        
        print()
        print("📊 JOB STATUS:")
        print("-" * 20)
        
        status = job_data.get('status', 'unknown')
        print(f"Status: {status.upper()}")
        
        if 'progress' in job_data:
            progress = job_data['progress']
            print(f"Progress: {progress}%")
        
        if 'created_at' in job_data:
            print(f"Created: {job_data['created_at']}")
        
        if 'updated_at' in job_data:
            print(f"Updated: {job_data['updated_at']}")
        
        if status in ['completed', 'success']:
            print()
            print("✅ Job completed successfully!")
            
            if 'results' in job_data:
                results = job_data['results']
                print()
                print("📋 RESULTS SUMMARY:")
                print("-" * 20)
                
                if 'codes_identified' in results:
                    print(f"Codes identified: {len(results['codes_identified'])}")

                if 'key_themes' in results:
                    print(f"Themes found: {len(results['key_themes'])}")

                if 'recommendations' in results:
                    print(f"Recommendations: {len(results['recommendations'])}")
        
        elif status in ['failed', 'error']:
            print()
            print("❌ Job failed!")
            if 'error' in job_data:
                print(f"Error: {job_data['error']}")
        
        elif status in ['running', 'processing', 'in_progress']:
            print()
            print("⏳ Job is still running...")
            print("You can monitor progress with:")
            print(f"  qc_cli analyze --watch-job {job_id}")
        
        else:
            print()
            print("❓ Job status unknown or pending")
        
        return 0
        
    except APIClientError as e:
        print(f"❌ Failed to get job status: {e}")
        return 1