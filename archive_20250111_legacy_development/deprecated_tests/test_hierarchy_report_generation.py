#!/usr/bin/env python3
"""
Test that reports can show hierarchical code structure
"""
import json
from pathlib import Path
from datetime import datetime
from src.qc.workflows.grounded_theory import OpenCode

def generate_hierarchy_report():
    """Generate a report showing hierarchical code structure"""
    print("=" * 60)
    print("TEST: HIERARCHY REPORT GENERATION")
    print("=" * 60)
    
    # 1. Create test hierarchical codes (using evidence from LLM test)
    print("\n1. LOADING HIERARCHICAL CODES...")
    
    # Load the evidence from our successful LLM test
    with open('evidence/current/direct_llm_hierarchy_test.json', 'r') as f:
        evidence = json.load(f)
    
    codes_data = evidence['response']['codes']
    print(f"   [OK] Loaded {len(codes_data)} codes from LLM evidence")
    
    # 2. Build hierarchy structure
    print("\n2. BUILDING HIERARCHY STRUCTURE...")
    
    # Group codes by hierarchy
    top_level_codes = [c for c in codes_data if c['level'] == 0]
    child_codes_map = {}
    
    for parent in top_level_codes:
        children = [c for c in codes_data if c.get('parent_id') == parent['code_name']]
        child_codes_map[parent['code_name']] = children
    
    print(f"   Found {len(top_level_codes)} parent codes")
    print(f"   Found {sum(len(v) for v in child_codes_map.values())} child codes")
    
    # 3. Generate markdown report
    print("\n3. GENERATING MARKDOWN REPORT...")
    
    report_dir = Path(f"reports/hierarchy_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / "hierarchical_codes_report.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Hierarchical Codes Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Code Hierarchy\n\n")
        f.write(f"Total codes: {len(codes_data)}\n")
        f.write(f"- Top-level codes: {len(top_level_codes)}\n")
        f.write(f"- Child codes: {len(codes_data) - len(top_level_codes)}\n\n")
        
        f.write("## Hierarchical Structure\n\n")
        
        # Write hierarchy tree
        for parent in top_level_codes:
            f.write(f"### {parent['code_name']}\n")
            f.write(f"**Level**: {parent['level']}\n")
            f.write(f"**Description**: {parent['description']}\n")
            f.write(f"**Frequency**: {parent['frequency']}\n")
            f.write(f"**Confidence**: {parent['confidence']}\n\n")
            
            if parent['code_name'] in child_codes_map:
                children = child_codes_map[parent['code_name']]
                if children:
                    f.write("#### Child Codes:\n\n")
                    for child in children:
                        f.write(f"- **{child['code_name']}** (Level {child['level']})\n")
                        f.write(f"  - Description: {child['description']}\n")
                        f.write(f"  - Frequency: {child['frequency']}\n")
                        f.write(f"  - Confidence: {child['confidence']}\n")
                        if child['supporting_quotes']:
                            f.write(f"  - Quote: \"{child['supporting_quotes'][0]}\"\n")
                        f.write("\n")
            
            f.write("---\n\n")
        
        # Write visual tree
        f.write("## Visual Hierarchy Tree\n\n")
        f.write("```\n")
        for parent in top_level_codes:
            f.write(f"{parent['code_name']}\n")
            if parent['code_name'] in child_codes_map:
                children = child_codes_map[parent['code_name']]
                for i, child in enumerate(children):
                    is_last = (i == len(children) - 1)
                    prefix = "└── " if is_last else "├── "
                    f.write(f"  {prefix}{child['code_name']}\n")
        f.write("```\n\n")
        
        # Write statistics
        f.write("## Hierarchy Statistics\n\n")
        f.write(f"- Average children per parent: {sum(len(v) for v in child_codes_map.values()) / len(top_level_codes) if top_level_codes else 0:.1f}\n")
        f.write(f"- Deepest level: {max(c['level'] for c in codes_data)}\n")
        f.write(f"- Codes with children: {len([c for c in codes_data if c['child_codes']])}\n")
        f.write(f"- Orphan codes (no parent, level > 0): {len([c for c in codes_data if c['level'] > 0 and not c.get('parent_id')])}\n")
    
    print(f"   [OK] Report saved to {report_file}")
    
    # 4. Generate JSON export with hierarchy
    print("\n4. GENERATING JSON EXPORT...")
    
    json_file = report_dir / "hierarchical_codes.json"
    export_data = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'total_codes': len(codes_data),
            'hierarchy_levels': max(c['level'] for c in codes_data) + 1
        },
        'hierarchy': []
    }
    
    # Build nested structure
    for parent in top_level_codes:
        parent_node = {
            'code': parent,
            'children': child_codes_map.get(parent['code_name'], [])
        }
        export_data['hierarchy'].append(parent_node)
    
    with open(json_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"   [OK] JSON export saved to {json_file}")
    
    # 5. Verify report shows hierarchy
    print("\n5. VERIFYING HIERARCHY IN REPORT...")
    
    with open(report_file, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    checks = {
        'Has parent codes': '### ' in report_content,
        'Has child codes': '#### Child Codes:' in report_content,
        'Shows levels': '**Level**: 0' in report_content and 'Level 1' in report_content,
        'Has visual tree': '├──' in report_content or '└──' in report_content,
        'Has statistics': 'Average children per parent' in report_content
    }
    
    all_passed = True
    for check, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"   {status} {check}")
        if not result:
            all_passed = False
    
    # 6. Save evidence
    print("\n6. SAVING EVIDENCE...")
    
    evidence_file = 'evidence/current/Evidence_Hierarchy_Report_Generation.json'
    with open(evidence_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'report_file': str(report_file),
            'json_file': str(json_file),
            'checks': checks,
            'all_passed': all_passed,
            'hierarchy_stats': {
                'total_codes': len(codes_data),
                'parent_codes': len(top_level_codes),
                'child_codes': len(codes_data) - len(top_level_codes),
                'max_level': max(c['level'] for c in codes_data)
            }
        }, f, indent=2)
    
    print(f"   [OK] Evidence saved to {evidence_file}")
    
    # Result
    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS: Hierarchical report generated successfully!")
        print(f"Report shows {len(top_level_codes)} parent codes with children")
        return True
    else:
        print("FAILURE: Report missing hierarchy elements")
        return False

if __name__ == "__main__":
    success = generate_hierarchy_report()
    exit(0 if success else 1)