#!/usr/bin/env python3
"""
QC Clean Architecture - Main Entry Point
"""

import sys
import asyncio
from pathlib import Path

# Ensure qc_clean is in the path for relative imports
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from core.cli.cli_robust import main

if __name__ == "__main__":
    # Run the async main function  
    exit_code = asyncio.run(main())
    sys.exit(exit_code)