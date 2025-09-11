#!/bin/bash
# Unix/Linux health check script

echo "Running Qualitative Coding Analysis Tool health check..."
echo

python3 scripts/validate_setup.py "$@"

echo
echo "For more information, see the detailed report in logs/"