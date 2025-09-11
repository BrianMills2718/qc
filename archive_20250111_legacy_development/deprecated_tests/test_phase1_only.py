#!/usr/bin/env python3
"""
Test only Phase 1 (Open Coding) to see what hierarchy is generated
"""
import asyncio
import json
from pathlib import Path
from src.qc.core.robust_cli_operations import RobustCLIOperations
from src.qc.config.methodology_config import MethodologyConfigManager
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow

async def test_phase1_only():
    """Test just Open Coding phase"""
    
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
    
    # Create workflow
    workflow = GroundedTheoryWorkflow(operations, config=config)
    
    # Run ONLY Phase 1
    print("Running Phase 1: Open Coding...")
    open_codes = await workflow.phase1_open_coding(interviews)
    
    print(f"\nGenerated {len(open_codes)} codes")
    
    # Analyze hierarchy
    levels = {}
    for code in open_codes:
        level = code.level
        levels[level] = levels.get(level, 0) + 1
    
    print(f"Level distribution: {levels}")
    print(f"Maximum depth: {max(levels.keys()) if levels else 0}")
    
    # Show some examples
    print("\nHierarchy Examples:")
    for code in open_codes[:10]:
        indent = "  " * code.level
        children_info = f" ({len(code.child_codes)} children)" if code.child_codes else ""
        print(f"{indent}L{code.level}: {code.code_name}{children_info}")
    
    # Save for inspection
    output = {
        'total_codes': len(open_codes),
        'level_distribution': levels,
        'codes': [
            {
                'name': c.code_name,
                'level': c.level,
                'parent_id': c.parent_id,
                'child_codes': c.child_codes
            }
            for c in open_codes
        ]
    }
    
    with open('phase1_hierarchy_test.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\nSaved to phase1_hierarchy_test.json")
    
    await operations.cleanup()
    
    return levels

if __name__ == "__main__":
    levels = asyncio.run(test_phase1_only())
    max_level = max(levels.keys()) if levels else 0
    if max_level >= 2:
        print(f"\nSUCCESS: Multi-level hierarchy with {max_level + 1} levels!")
    else:
        print(f"\nFAILED: Only {max_level + 1} levels generated")