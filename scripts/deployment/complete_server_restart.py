import subprocess
import time
import requests
import os
import sys
import shutil

def force_clean_environment():
    """Complete environment cleanup"""
    # Kill processes
    subprocess.run(['powershell', '-Command', 'Get-Process python* | Stop-Process -Force'], 
                  capture_output=True)
    
    # Clear cache
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(root, '__pycache__'), ignore_errors=True)
    
    time.sleep(3)

def start_server_clean():
    """Start server with completely fresh Python environment"""
    # Start with explicit cache clearing
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'  # Prevent cache creation
    
    process = subprocess.Popen(
        [sys.executable, '-B', 'start_dashboard.py'],  # -B flag prevents cache
        env=env
    )
    
    print(f"Started clean server with PID: {process.pid}")
    time.sleep(10)  # Longer startup time
    return process

def validate_complete_reload():
    """Validate server has ALL updated code"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/entity/AI/network", timeout=15)
        if response.status_code == 200:
            data = response.json()
            
            has_field = 'entity_relationships' in data.get('network', {})
            has_trace = 'trace_marker' in data
            trace_value = data.get('trace_marker', 'MISSING')
            
            print(f"VALIDATION RESULTS:")
            print(f"  Field present: {has_field}")
            print(f"  Trace marker: {trace_value}")
            
            # SUCCESS requires BOTH field AND trace markers
            return has_field and trace_value == 'FIXED_FUNCTION_ACTIVE_v2025_08_07'
    except Exception as e:
        print(f"Validation error: {e}")
        return False

if __name__ == "__main__":
    force_clean_environment()
    process = start_server_clean()
    success = validate_complete_reload()
    
    if success:
        print("SUCCESS: Complete server reload achieved")
    else:
        print("FAILURE: Server still running mixed code")