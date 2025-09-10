#!/usr/bin/env python3
"""
Simple import tracing for GT analysis runtime dependencies
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Track imports by monitoring sys.modules before and after
print("Capturing baseline modules...")
baseline_modules = set(sys.modules.keys())

# Import and run a minimal GT test
print("Running GT analysis...")
try:
    from src.qc.cli_robust import main
    from src.qc.core.robust_cli_operations import RobustCLIOperations
    
    # Simulate the analyze command
    sys.argv = ["cli_robust", "analyze", 
                "--input", "data/interviews/ai_interviews_3_for_test",
                "--output", "reports/baseline_verification"]
    
    # Run analysis
    main()
    
except Exception as e:
    print(f"Analysis failed: {e}")

# Get modules imported during GT analysis
new_modules = set(sys.modules.keys()) - baseline_modules
qc_modules = [m for m in new_modules if 'src.qc' in m or m.startswith('qc')]

print(f"\nTotal new modules loaded: {len(new_modules)}")
print(f"QC-specific modules loaded: {len(qc_modules)}")
print("\nQC modules imported during analysis:")
for module in sorted(qc_modules):
    print(f"  - {module}")

# Also check which files were actually accessed
print(f"\nCore QC modules found in sys.modules:")
core_qc = [m for m in sys.modules.keys() if m.startswith('src.qc')]
print(f"Total: {len(core_qc)} modules")
for module in sorted(core_qc)[:20]:  # Show first 20
    print(f"  - {module}")
if len(core_qc) > 20:
    print(f"  ... and {len(core_qc) - 20} more")