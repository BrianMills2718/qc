#!/usr/bin/env python3
"""
Dashboard Startup Script for Qualitative Coding System
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Add project root for qc_clean imports
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print("Starting Qualitative Coding Dashboard...")
    print("Dashboard will be available at: http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    
    # Start the FastAPI server
    uvicorn.run(
        "web_interface.app:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        log_level="info"
    )