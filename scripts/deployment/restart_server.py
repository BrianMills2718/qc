#!/usr/bin/env python3
"""
Force restart server to pick up code changes
"""

import subprocess
import time
import os
import signal
import psutil
import sys

def kill_existing_servers():
    """Kill any existing Python servers on port 8000"""
    print("Killing existing server processes...")
    
    # Find processes using port 8000
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if it's a Python process with our server
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'start_dashboard.py' in cmdline or ':8000' in cmdline:
                    print(f"Killing process {proc.info['pid']}: {cmdline}")
                    proc.kill()
                    proc.wait()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Additional cleanup - kill by port
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if ':8000' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    try:
                        subprocess.run(['taskkill', '/F', '/PID', pid], check=False)
                        print(f"Killed process using port 8000: PID {pid}")
                    except:
                        pass
    except:
        print("Could not check netstat")
    
    time.sleep(2)  # Wait for processes to die

def start_server():
    """Start the dashboard server"""
    print("Starting fresh server...")
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Start server
    try:
        subprocess.Popen([sys.executable, 'start_dashboard.py'], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        print("Server started. Waiting for startup...")
        time.sleep(5)
        return True
    except Exception as e:
        print(f"Failed to start server: {e}")
        return False

def test_server():
    """Test that server is responding with updated code"""
    import requests
    
    try:
        # Test the test endpoint first
        response = requests.get("http://127.0.0.1:8000/api/test-server-update", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'UPDATED_CODE_WORKING':
                print("✅ Server is running UPDATED code!")
                return True
        print("⚠️  Server running but may have old code")
        return False
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False

def main():
    """Main restart process"""
    print("🚀 FORCE SERVER RESTART")
    print("=" * 30)
    
    kill_existing_servers()
    
    if start_server():
        if test_server():
            print("\n✅ Server restart successful!")
            return True
        else:
            print("\n⚠️  Server started but may have issues")
            return False
    else:
        print("\n❌ Server restart failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)