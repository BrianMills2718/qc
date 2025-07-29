#!/usr/bin/env python
"""
Run full AI interviews analysis with UTF-8 log encoding.
This wrapper ensures proper encoding for Windows PowerShell.
"""
import subprocess
import sys
import io

def main():
    # Set up UTF-8 encoding for stdout and stderr
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    # Run the actual analysis script
    result = subprocess.run(
        [sys.executable, 'run_full_ai_analysis.py'],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    # Print output with proper encoding
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())