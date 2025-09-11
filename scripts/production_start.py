#!/usr/bin/env python3
"""
Production Dashboard Startup Script
Qualitative Coding Analysis Dashboard - Production Mode
"""

import uvicorn
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add src directory to Python path for imports
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(project_root))

def main():
    """Start the production dashboard"""
    
    print("=" * 60)
    print("QUALITATIVE CODING ANALYSIS DASHBOARD")
    print("=" * 60)
    print("Starting Qualitative Coding Dashboard in Production Mode...")
    print()
    print("Dashboard Features:")
    print("  - Interactive entity and code exploration")
    print("  - Quote browsing and analysis")
    print("  - Pattern analytics and insights")
    print("  - Export functionality")
    print("  - Natural language query interface")
    print()
    print("Access Information:")
    print("  Dashboard URL: http://127.0.0.1:8000")
    print("  Health Check:  http://127.0.0.1:8000/health")
    print("  API Docs:      http://127.0.0.1:8000/docs")
    print()
    print("Usage Instructions:")
    print("  1. Open http://127.0.0.1:8000 in your web browser")
    print("  2. Explore the main dashboard for system overview")
    print("  3. Use Entity Explorer to browse research entities")
    print("  4. Check Quote Browser for detailed quote analysis")
    print("  5. Use Export tools for data extraction")
    print()
    print("Note: Neo4j authentication integration in progress")
    print("   Dashboard UI functional, database integration being refined")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Start the FastAPI server in production mode
    uvicorn.run(
        "web_interface.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Production mode - no auto-reload
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()