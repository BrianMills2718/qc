#!/usr/bin/env python3
"""
Test that LLM actually populates hierarchy fields in OpenCode objects
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from src.qc.core.robust_cli_operations import RobustCLIOperations
from src.qc.config.methodology_config import MethodologyConfigManager
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow

async def test_llm_hierarchy_population():
    """Test that LLM populates hierarchy fields"""
    print("=" * 60)
    print("TEST: LLM HIERARCHY POPULATION")
    print("=" * 60)
    
    # 1. Initialize
    print("\n1. INITIALIZING...")
    config_manager = MethodologyConfigManager()
    config = config_manager.load_config_from_path(
        Path('config/methodology_configs/grounded_theory_reliable.yaml')
    )
    
    operations = RobustCLIOperations(config=config)
    await operations.initialize_systems()
    print("   [OK] Systems initialized")
    
    # 2. Load test data
    print("\n2. LOADING TEST DATA...")
    interviews = operations.robust_load_interviews(
        Path('data/interviews/ai_interviews_3_for_test')
    )
    print(f"   [OK] Loaded {len(interviews)} interviews")
    
    # 3. Run ONLY open coding phase to check hierarchy
    print("\n3. RUNNING OPEN CODING PHASE ONLY...")
    workflow = GroundedTheoryWorkflow(operations, config=config)
    
    try:
        # Call _open_coding_phase directly to avoid timeout
        open_codes = await workflow._open_coding_phase(interviews)
        print(f"   [OK] Open coding completed, generated {len(open_codes)} codes")
        
        # Create minimal result object
        result = type('Result', (), {
            'open_codes': open_codes,
            'core_categories': [],
            'theoretical_model': None
        })()
    except Exception as e:
        print(f"   [ERROR] Open coding failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Check hierarchy in codes
    print("\n4. CHECKING HIERARCHY IN CODES...")
    
    hierarchical_codes = []
    flat_codes = []
    
    for code in result.open_codes:
        has_hierarchy = (
            code.parent_id is not None or 
            len(code.child_codes) > 0 or 
            code.level > 0
        )
        
        if has_hierarchy:
            hierarchical_codes.append(code)
        else:
            flat_codes.append(code)
    
    print(f"   Total codes: {len(result.open_codes)}")
    print(f"   Hierarchical codes: {len(hierarchical_codes)}")
    print(f"   Flat codes: {len(flat_codes)}")
    
    # 5. Save evidence
    print("\n5. SAVING EVIDENCE...")
    
    # Save codes to JSON
    evidence_dir = Path("evidence/current")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    codes_data = []
    for code in result.open_codes:
        codes_data.append({
            'code_name': code.code_name,
            'description': code.description,
            'parent_id': code.parent_id,
            'level': code.level,
            'child_codes': code.child_codes,
            'frequency': code.frequency,
            'confidence': code.confidence
        })
    
    json_file = evidence_dir / f"llm_codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w') as f:
        json.dump(codes_data, f, indent=2)
    print(f"   [OK] Saved codes to {json_file}")
    
    # 6. Generate evidence report
    print("\n6. GENERATING EVIDENCE REPORT...")
    
    report_file = evidence_dir / "Evidence_LLM_Hierarchy_Population.md"
    with open(report_file, 'w') as f:
        f.write("# Evidence: LLM Hierarchy Population\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Test**: test_llm_hierarchy_population.py\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- Total codes generated: {len(result.open_codes)}\n")
        f.write(f"- Codes with hierarchy: {len(hierarchical_codes)}\n")
        f.write(f"- Flat codes: {len(flat_codes)}\n")
        f.write(f"- **Hierarchy detected**: {'YES' if hierarchical_codes else 'NO'}\n\n")
        
        if hierarchical_codes:
            f.write("## Hierarchical Codes Found\n\n")
            for code in hierarchical_codes[:5]:  # Show first 5
                f.write(f"### {code.code_name}\n")
                f.write(f"- **Parent ID**: {code.parent_id or 'None'}\n")
                f.write(f"- **Level**: {code.level}\n")
                f.write(f"- **Child codes**: {', '.join(code.child_codes) if code.child_codes else 'None'}\n")
                f.write(f"- **Description**: {code.description}\n\n")
        else:
            f.write("## Issue: No Hierarchical Codes Found\n\n")
            f.write("The LLM did not populate hierarchy fields. Sample codes:\n\n")
            for code in flat_codes[:3]:
                f.write(f"- **{code.code_name}**: level={code.level}, parent={code.parent_id}\n")
        
        f.write(f"\n## Evidence File\n")
        f.write(f"Raw codes saved to: `{json_file}`\n")
    
    print(f"   [OK] Report saved to {report_file}")
    
    # 7. Final result
    print("\n" + "=" * 60)
    if hierarchical_codes:
        print("SUCCESS: LLM populated hierarchy fields")
        print(f"Found {len(hierarchical_codes)} codes with hierarchical structure")
        return True
    else:
        print("FAILURE: LLM did not populate hierarchy fields")
        print("All codes are flat (no parent_id, level=0, no children)")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_hierarchy_population())
    exit(0 if success else 1)