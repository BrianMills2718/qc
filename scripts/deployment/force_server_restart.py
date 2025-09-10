"""Force server restart with cache clearing"""
import subprocess
import psutil
import time
import requests
import shutil
import os
import sys

def kill_existing_servers():
    """Kill processes using port 8000"""
    print("SEARCHING: Looking for existing server processes...")
    killed_any = False
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'connections']):
        try:
            # Check if process is using port 8000
            connections = proc.info.get('connections', [])
            uses_port_8000 = any(
                hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == 8000
                for conn in connections
            )
            
            if uses_port_8000:
                print(f"FOUND: Process using port 8000: PID {proc.info['pid']} ({proc.info['name']})")
                proc.kill()
                proc.wait()
                killed_any = True
                print(f"KILLED: Process {proc.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            pass
    
    # Also kill any Python processes running start_dashboard.py
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if (proc.info['name'] and 'python' in proc.info['name'].lower() and 
                proc.info['cmdline'] and any('start_dashboard.py' in str(arg) for arg in proc.info['cmdline'])):
                print(f"FOUND: Dashboard process: PID {proc.info['pid']}")
                proc.kill()
                proc.wait()
                killed_any = True
                print(f"KILLED: Dashboard process {proc.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            pass
    
    if not killed_any:
        print("INFO: No existing server processes found")
    
    time.sleep(2)  # Give processes time to fully terminate
    return killed_any

def clear_python_cache():
    """Clear Python cache files"""
    print("🧹 Clearing Python cache files...")
    cache_dirs_cleared = 0
    
    # Clear __pycache__ directories
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                cache_dirs_cleared += 1
                print(f"✅ Cleared cache: {cache_dir}")
            except Exception as e:
                print(f"⚠️ Failed to clear {cache_dir}: {e}")
    
    print(f"🧹 Cleared {cache_dirs_cleared} cache directories")

def start_fresh_server():
    """Start server with fresh module loading"""
    print("🚀 Starting fresh server...")
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Start server with unbuffered output
    process = subprocess.Popen(
        [sys.executable, 'start_dashboard.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    print(f"🚀 Started server process with PID: {process.pid}")
    
    # Give server time to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    return process

def validate_server():
    """Test server is running updated code"""
    print("🔍 Validating server is running updated code...")
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"📡 Attempt {attempt + 1}: Testing server connection...")
            response = requests.get("http://127.0.0.1:8000/api/entity/AI/network", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_field = 'entity_relationships' in data.get('network', {})
                has_trace = 'trace_marker' in data
                trace_value = data.get('trace_marker', 'MISSING')
                
                print(f"📊 Response analysis:")
                print(f"   - Status: {response.status_code}")
                print(f"   - Trace marker: {trace_value}")
                print(f"   - entity_relationships field: {has_field}")
                
                if has_field and has_trace:
                    rel_count = len(data.get('network', {}).get('entity_relationships', []))
                    print(f"   - Relationship count: {rel_count}")
                    print("✅ SERVER RESTART SUCCESSFUL - Updated code is running!")
                    return True
                else:
                    print("⚠️ Server responding but still using old code")
            else:
                print(f"⚠️ Server responded with status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"⚠️ Connection failed (attempt {attempt + 1})")
        except requests.exceptions.Timeout:
            print(f"⚠️ Request timeout (attempt {attempt + 1})")
        except Exception as e:
            print(f"⚠️ Validation error: {e}")
        
        if attempt < max_retries - 1:
            print("⏳ Waiting 3 seconds before retry...")
            time.sleep(3)
    
    print("❌ Server restart failed - could not validate updated code")
    return False

def main():
    print("FORCE SERVER RESTART WITH CACHE CLEARING")
    print("=" * 50)
    
    try:
        # Step 1: Kill existing servers
        kill_existing_servers()
        
        # Step 2: Clear Python cache
        clear_python_cache()
        
        # Step 3: Start fresh server
        server_process = start_fresh_server()
        
        # Step 4: Validate server
        success = validate_server()
        
        if success:
            print("\n🎉 SUCCESS: Server restart completed successfully!")
            print("✅ Live API is now running the updated code with entity_relationships field")
            print("🚀 You can now test the network visualization in the frontend")
            return True
        else:
            print("\n❌ FAILURE: Server restart did not resolve the issue")
            print("🔍 The live API is still not running the updated code")
            if server_process and server_process.poll() is None:
                print("⚠️ Terminating failed server process...")
                server_process.terminate()
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error during restart: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 TROUBLESHOOTING SUGGESTIONS:")
        print("   1. Check if another process is using port 8000")
        print("   2. Try manually stopping all Python processes")
        print("   3. Restart your terminal/IDE")
        print("   4. Check for permission issues with cache directories")
        sys.exit(1)