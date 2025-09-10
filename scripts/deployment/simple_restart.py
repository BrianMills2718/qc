"""Simple server restart script"""
import subprocess
import time
import requests
import shutil
import os
import sys

def kill_server():
    """Kill server on port 8000"""
    print("KILLING: Terminating server on port 8000...")
    try:
        # Kill process on port 8000 on Windows
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                      capture_output=True, text=True)
        subprocess.run(['taskkill', '/F', '/IM', 'python3.11.exe'], 
                      capture_output=True, text=True)
        print("KILLED: Terminated Python processes")
    except Exception as e:
        print(f"WARNING: Could not kill processes: {e}")
    
    time.sleep(3)

def clear_cache():
    """Clear Python cache"""
    print("CLEARING: Removing Python cache files...")
    try:
        cache_count = 0
        for root, dirs, files in os.walk('.'):
            if '__pycache__' in dirs:
                cache_dir = os.path.join(root, '__pycache__')
                shutil.rmtree(cache_dir)
                cache_count += 1
        print(f"CLEARED: {cache_count} cache directories")
    except Exception as e:
        print(f"WARNING: Cache clearing failed: {e}")

def start_server():
    """Start server"""
    print("STARTING: Launching fresh server...")
    try:
        process = subprocess.Popen([sys.executable, 'start_dashboard.py'])
        print(f"STARTED: Server process PID {process.pid}")
        time.sleep(8)
        return process
    except Exception as e:
        print(f"ERROR: Failed to start server: {e}")
        return None

def test_server():
    """Test if server works"""
    print("TESTING: Validating server response...")
    try:
        response = requests.get("http://127.0.0.1:8000/api/entity/AI/network", timeout=15)
        if response.status_code == 200:
            data = response.json()
            has_trace = 'trace_marker' in data
            has_field = 'entity_relationships' in data.get('network', {})
            trace_value = data.get('trace_marker', 'MISSING')
            
            print(f"RESULT: Status {response.status_code}")
            print(f"RESULT: Trace marker = {trace_value}")
            print(f"RESULT: entity_relationships field = {has_field}")
            
            if has_field and has_trace:
                rel_count = len(data.get('network', {}).get('entity_relationships', []))
                print(f"SUCCESS: Found {rel_count} relationships")
                return True
            else:
                print("FAILURE: Still using old code")
                return False
        else:
            print(f"FAILURE: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"FAILURE: Request failed: {e}")
        return False

def main():
    print("SERVER RESTART UTILITY")
    print("=" * 30)
    
    # Step 1: Kill existing server
    kill_server()
    
    # Step 2: Clear cache
    clear_cache()
    
    # Step 3: Start server
    process = start_server()
    if not process:
        print("ABORT: Could not start server")
        return False
    
    # Step 4: Test server
    success = test_server()
    
    if success:
        print("SUCCESS: Server restart completed!")
        print("READY: Network visualization should now work")
    else:
        print("FAILURE: Restart did not fix the issue")
        
    return success

if __name__ == "__main__":
    main()