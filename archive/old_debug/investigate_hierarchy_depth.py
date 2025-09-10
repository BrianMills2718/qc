#!/usr/bin/env python3
"""
Investigate the actual hierarchy depth in the generated codes
"""
import asyncio
import json
from pathlib import Path
from src.qc.core.robust_cli_operations import RobustCLIOperations
from src.qc.config.methodology_config import MethodologyConfigManager
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow

async def investigate_hierarchy():
    """Deep investigation of hierarchy in generated codes"""
    print("=" * 60)
    print("HIERARCHY DEPTH INVESTIGATION")
    print("=" * 60)
    
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
    print("\n1. RUNNING GT WORKFLOW...")
    workflow = GroundedTheoryWorkflow(operations, config=config)
    
    try:
        results = await workflow.execute_complete_workflow(interviews)
        
        if results and results.open_codes:
            print(f"   Generated {len(results.open_codes)} codes")
            
            # Analyze hierarchy structure
            print("\n2. ANALYZING HIERARCHY STRUCTURE...")
            
            # Count codes by level
            level_counts = {}
            for code in results.open_codes:
                level = code.level
                level_counts[level] = level_counts.get(level, 0) + 1
            
            print("\n   Codes by hierarchy level:")
            for level in sorted(level_counts.keys()):
                print(f"      Level {level}: {level_counts[level]} codes")
            
            # Find parent-child relationships
            print("\n3. PARENT-CHILD RELATIONSHIPS:")
            
            parent_codes = [c for c in results.open_codes if c.child_codes]
            print(f"   Parent codes (have children): {len(parent_codes)}")
            
            for parent in parent_codes[:5]:  # Show first 5
                print(f"\n   Parent: {parent.code_name}")
                print(f"      Level: {parent.level}")
                print(f"      Child IDs: {parent.child_codes}")
                
                # Find actual child objects
                for child_id in parent.child_codes:
                    # Try different matching strategies
                    children = [c for c in results.open_codes 
                              if c.code_name == child_id 
                              or c.code_name.replace(' ', '_') == child_id
                              or c.code_name == child_id.replace('_', ' ')]
                    
                    if children:
                        child = children[0]
                        print(f"      └─ Child: {child.code_name}")
                        print(f"         Level: {child.level}")
                        print(f"         Parent ID: {child.parent_id}")
                        
                        # Check for grandchildren
                        if child.child_codes:
                            print(f"         Has {len(child.child_codes)} grandchildren!")
                            for gc_id in child.child_codes:
                                print(f"            - {gc_id}")
                    else:
                        print(f"      └─ Child ID '{child_id}' not found in codes!")
            
            # Check for orphans (codes with parent_id but parent doesn't exist)
            print("\n4. ORPHAN ANALYSIS:")
            orphans = []
            for code in results.open_codes:
                if code.parent_id:
                    parent_exists = any(
                        p.code_name == code.parent_id 
                        or p.code_name.replace(' ', '_') == code.parent_id
                        for p in results.open_codes
                    )
                    if not parent_exists:
                        orphans.append(code)
            
            print(f"   Orphan codes (parent_id set but parent not found): {len(orphans)}")
            for orphan in orphans[:3]:
                print(f"      - {orphan.code_name} (parent_id: {orphan.parent_id})")
            
            # Check maximum depth
            print("\n5. MAXIMUM HIERARCHY DEPTH:")
            max_level = max(c.level for c in results.open_codes) if results.open_codes else 0
            print(f"   Maximum level found: {max_level}")
            
            # Save raw data for inspection
            print("\n6. SAVING RAW DATA...")
            output_file = Path("investigation_hierarchy_data.json")
            
            codes_data = []
            for code in results.open_codes:
                codes_data.append({
                    'code_name': code.code_name,
                    'level': code.level,
                    'parent_id': code.parent_id,
                    'child_codes': code.child_codes,
                    'frequency': code.frequency
                })
            
            with open(output_file, 'w') as f:
                json.dump({
                    'total_codes': len(results.open_codes),
                    'level_counts': level_counts,
                    'max_level': max_level,
                    'parent_codes_count': len(parent_codes),
                    'orphans_count': len(orphans),
                    'codes': codes_data
                }, f, indent=2)
            
            print(f"   Saved to {output_file}")
            
        else:
            print("   ERROR: No codes generated")
            
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await operations.cleanup()

if __name__ == "__main__":
    asyncio.run(investigate_hierarchy())