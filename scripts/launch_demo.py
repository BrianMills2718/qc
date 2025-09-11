#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-Click Demo Launcher
Automatically sets up and launches the qualitative coding analysis tool demo
"""
import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def launch_demo():
    """Launch demo with automatic browser opening"""
    root_dir = Path(__file__).parent.parent
    
    print("🚀 Launching Qualitative Coding Analysis Tool Demo...")
    print("="*60)
    
    # Run demo setup
    setup_script = root_dir / "scripts" / "demo_setup.py"
    print("📋 Running demo setup...")
    
    try:
        result = subprocess.run([sys.executable, str(setup_script)], 
                              cwd=root_dir, check=True)
    except subprocess.CalledProcessError:
        print("❌ Demo setup failed")
        sys.exit(1)
    
    print("\n🌐 Starting web server...")
    
    # Change to root directory
    os.chdir(root_dir)
    
    # Start server in background and open browser
    try:
        print("   Starting server at http://localhost:8000")
        
        # Start server process
        server_process = subprocess.Popen([
            sys.executable, "-m", "src.qc.cli", "serve", 
            "--host", "127.0.0.1", "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        print("   Waiting for server startup...")
        time.sleep(3)
        
        # Check if server is running
        if server_process.poll() is None:
            print("✅ Server started successfully")
            print("🌐 Opening browser...")
            
            # Open browser
            webbrowser.open("http://localhost:8000")
            
            print("\n" + "="*60)
            print("🎉 DEMO IS NOW RUNNING!")
            print("="*60)
            print("📱 Web Interface: http://localhost:8000")
            print("📚 API Documentation: http://localhost:8000/docs")
            print("📊 Pre-loaded: 3 AI research interviews fully analyzed")
            print("🔍 Explore: 30+ themes, entity networks, dialogue analysis")
            print("\n💡 Demo Guide: See DEMO.md for full walkthrough")
            print("⌨️  Press Ctrl+C to stop the demo server")
            print("="*60)
            
            # Keep running until interrupted
            try:
                server_process.wait()
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping demo server...")
                server_process.terminate()
                server_process.wait()
                print("✅ Demo server stopped")
                
        else:
            # Server failed to start
            stdout, stderr = server_process.communicate()
            print("❌ Server failed to start")
            if stderr:
                print(f"Error: {stderr.decode()}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error launching demo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    launch_demo()