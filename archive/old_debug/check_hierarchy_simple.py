#!/usr/bin/env python3
"""
Simple check of hierarchy depth without unicode issues
"""
import asyncio
import json
from pathlib import Path
from src.qc.core.robust_cli_operations import RobustCLIOperations
from src.qc.config.methodology_config import MethodologyConfigManager
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow

async def check_hierarchy():
    """Check hierarchy depth in generated codes"""
    # Initialize
    config_manager = MethodologyConfigManager()
    config = config_manager.load_config_from_path(
        Path('config/methodology_configs/grounded_theory_reliable.yaml')
    )
    
    operations = RobustCLIOperations(config=config)
    await operations.initialize_systems()
    
    # Load interviews
    interviews = operations.robust_load_interviews(
        Path('data/interviews/ai_interviews_3_for_test')
    )
    
    # Run workflow
    print("Running GT workflow...")
    workflow = GroundedTheoryWorkflow(operations, config=config)
    
    results = await workflow.execute_complete_workflow(interviews)
    
    if results and results.open_codes:
        print(f"\nTotal codes: {len(results.open_codes)}")
        
        # Count by level
        level_counts = {}
        for code in results.open_codes:
            level = code.level
            level_counts[level] = level_counts.get(level, 0) + 1
        
        print("\nHierarchy levels found:")
        for level in sorted(level_counts.keys()):
            print(f"  Level {level}: {level_counts[level]} codes")
        
        # Check for multi-level hierarchy
        max_level = max(level_counts.keys()) if level_counts else 0
        print(f"\nMaximum hierarchy depth: {max_level}")
        
        if max_level == 0:
            print("ISSUE: All codes are at level 0 (no hierarchy)")
        elif max_level == 1:
            print("ISSUE: Only 2-level hierarchy (parents and children, no grandchildren)")
        else:
            print(f"SUCCESS: Multi-level hierarchy with {max_level + 1} levels")
        
        # Check parent-child linkage
        print("\nParent-Child Linkage Analysis:")
        
        # Find codes with children
        parents_with_children = [c for c in results.open_codes if c.child_codes]
        print(f"  Codes with child_codes field populated: {len(parents_with_children)}")
        
        # Find codes with parent_id
        children_with_parents = [c for c in results.open_codes if c.parent_id]
        print(f"  Codes with parent_id field populated: {len(children_with_parents)}")
        
        # Check if any level 1 codes have children (would create level 2)
        level1_with_children = [c for c in results.open_codes 
                                if c.level == 1 and c.child_codes]
        print(f"  Level 1 codes that have children: {len(level1_with_children)}")
        
        if level1_with_children:
            print("  Examples of potential 3-level hierarchy:")
            for code in level1_with_children[:3]:
                print(f"    - {code.code_name} has {len(code.child_codes)} children")
        
        # Save simplified data
        data = {
            'total_codes': len(results.open_codes),
            'level_distribution': level_counts,
            'max_depth': max_level,
            'parents_count': len(parents_with_children),
            'children_count': len(children_with_parents),
            'potential_3_level': len(level1_with_children),
            'codes': [
                {
                    'name': c.code_name,
                    'level': c.level,
                    'parent_id': c.parent_id,
                    'child_codes': c.child_codes
                }
                for c in results.open_codes
            ]
        }
        
        with open('hierarchy_analysis.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print("\nData saved to hierarchy_analysis.json")
        
    await operations.cleanup()

if __name__ == "__main__":
    asyncio.run(check_hierarchy())