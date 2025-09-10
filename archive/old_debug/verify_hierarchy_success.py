#!/usr/bin/env python3
"""
Verify that hierarchical codes were successfully generated
"""
import json
from pathlib import Path

# Check most recent memo for structure
memo_files = sorted(Path('data/memos').glob('theoretical_memo_*.json'))
if memo_files:
    latest_memo = memo_files[-1]
    print(f"Checking memo: {latest_memo.name}")
    
    with open(latest_memo) as f:
        data = json.load(f)
    
    # Check for codes
    if 'codes' in data:
        codes = data['codes']
        print(f"\nTotal codes found: {len(codes)}")
        
        # Check for hierarchy
        hierarchical = [c for c in codes if c.get('parent_id') or c.get('level', 0) > 0]
        if hierarchical:
            print(f"Hierarchical codes: {len(hierarchical)}")
            for code in hierarchical[:3]:
                print(f"  - {code.get('name', 'unnamed')} (level={code.get('level', 0)}, parent={code.get('parent_id')})")
        else:
            print("No hierarchical structure found in codes")
            
        # Check for parent codes with children
        parent_codes = [c for c in codes if c.get('child_codes')]
        if parent_codes:
            print(f"\nParent codes with children: {len(parent_codes)}")
            for parent in parent_codes[:3]:
                print(f"  - {parent.get('name', 'unnamed')} has {len(parent.get('child_codes', []))} children")
else:
    print("No memo files found")