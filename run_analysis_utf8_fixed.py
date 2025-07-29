#!/usr/bin/env python3
"""
UTF-8 wrapper for Windows to ensure proper log encoding.
This fixes the UTF-16 encoding issue in Windows PowerShell.
"""
import sys
import io
import os

# Force UTF-8 for Windows
if sys.platform == 'win32':
    # Set console code page to UTF-8
    os.system('chcp 65001 > nul')
    
    # Force Python to use UTF-8 for stdout/stderr
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, 
        encoding='utf-8', 
        errors='replace',
        line_buffering=True
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, 
        encoding='utf-8', 
        errors='replace',
        line_buffering=True
    )
    
    # Also set environment variable
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Now import and run the actual analysis
if __name__ == "__main__":
    # Import here to ensure encoding is set first
    from run_full_ai_analysis import main
    import asyncio
    
    # Run the main function
    asyncio.run(main())