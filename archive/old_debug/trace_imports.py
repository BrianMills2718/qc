#!/usr/bin/env python3
"""
Import tracing utility to track actual file imports during GT analysis
"""
import sys
import importlib.util
from collections import defaultdict
import time

class ImportTracker:
    def __init__(self):
        self.imported_modules = set()
        self.import_times = {}
        self.import_tree = defaultdict(list)
        self.original_import = __builtins__['__import__']
        
    def track_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        """Custom import function to track module loading"""
        start_time = time.time()
        
        # Call original import
        module = self.original_import(name, globals, locals, fromlist, level)
        
        # Track the import
        if name.startswith('src.qc') or name.startswith('qc'):
            self.imported_modules.add(name)
            self.import_times[name] = time.time() - start_time
            
            # Track import hierarchy
            if globals and '__name__' in globals:
                parent = globals['__name__']
                if parent.startswith('src.qc') or parent.startswith('qc'):
                    self.import_tree[parent].append(name)
        
        return module
    
    def start_tracking(self):
        """Start import tracking"""
        __builtins__['__import__'] = self.track_import
        
    def stop_tracking(self):
        """Stop import tracking"""
        __builtins__['__import__'] = self.original_import
        
    def get_results(self):
        """Get tracking results"""
        return {
            'imported_modules': sorted(list(self.imported_modules)),
            'import_count': len(self.imported_modules),
            'total_time': sum(self.import_times.values()),
            'import_tree': dict(self.import_tree)
        }

if __name__ == "__main__":
    tracker = ImportTracker()
    tracker.start_tracking()
    
    print("Starting import tracking...")
    
    try:
        # Import and run GT analysis
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "src.qc.cli_robust", "analyze",
            "--input", "data/interviews/ai_interviews_3_for_test", 
            "--output", "reports/baseline_verification"
        ], capture_output=True, text=True, cwd=".")
        
        print("GT Analysis completed")
        print(f"Return code: {result.returncode}")
        if result.stderr:
            print(f"Errors: {result.stderr[:500]}...")
            
    finally:
        tracker.stop_tracking()
        
    results = tracker.get_results()
    
    print(f"\nImport Tracking Results:")
    print(f"Total modules imported: {results['import_count']}")
    print(f"Total import time: {results['total_time']:.3f}s")
    print(f"\nImported modules:")
    for module in results['imported_modules']:
        print(f"  - {module}")