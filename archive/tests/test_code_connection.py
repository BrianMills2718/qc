"""
Test to verify that quotes reference valid taxonomy codes
This test demonstrates the disconnect between taxonomy and quote codes
"""

import json
from pathlib import Path
import sys

def test_code_connections(output_dir="output_performance_optimized"):
    """Verify that quotes reference valid taxonomy codes"""
    print(f"\n{'='*60}")
    print(f"Testing Code Connections in: {output_dir}")
    print(f"{'='*60}")
    
    # Load taxonomy
    taxonomy_file = Path(output_dir) / "taxonomy.json"
    if not taxonomy_file.exists():
        print(f"ERROR: Taxonomy file not found: {taxonomy_file}")
        return False
    
    with open(taxonomy_file, 'r', encoding='utf-8') as f:
        taxonomy = json.load(f)
    
    code_ids = {c['id'] for c in taxonomy['codes']}
    code_names = {c['name'] for c in taxonomy['codes']}
    
    print(f"\nTaxonomy Statistics:")
    print(f"  - Total codes: {len(code_ids)}")
    print(f"  - Sample IDs: {list(code_ids)[:3]}")
    print(f"  - Sample names: {list(code_names)[:3]}")
    
    # Load interviews
    interviews_dir = Path(output_dir) / "interviews"
    if not interviews_dir.exists():
        print(f"ERROR: Interviews directory not found: {interviews_dir}")
        return False
    
    total_quotes = 0
    quotes_with_codes = 0
    all_quote_code_ids = set()
    invalid_code_ids = set()
    
    for interview_file in interviews_dir.glob("*.json"):
        with open(interview_file, 'r', encoding='utf-8') as f:
            interview = json.load(f)
        
        print(f"\nInterview: {interview_file.stem}")
        interview_quotes = len(interview['quotes'])
        interview_coded = 0
        
        for quote in interview['quotes']:
            total_quotes += 1
            quote_code_ids = quote.get('code_ids', [])
            
            if quote_code_ids:
                quotes_with_codes += 1
                interview_coded += 1
                
                # Check if codes are valid
                for code_id in quote_code_ids:
                    all_quote_code_ids.add(code_id)
                    if code_id not in code_ids:
                        invalid_code_ids.add(code_id)
                        print(f"    X Invalid code ID: {code_id}")
        
        print(f"  - Total quotes: {interview_quotes}")
        print(f"  - Quotes with codes: {interview_coded} ({interview_coded/interview_quotes*100:.1f}%)")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total quotes across all interviews: {total_quotes}")
    print(f"Quotes with codes: {quotes_with_codes} ({quotes_with_codes/total_quotes*100:.1f}%)")
    print(f"Unique code IDs used in quotes: {len(all_quote_code_ids)}")
    print(f"Invalid code IDs found: {len(invalid_code_ids)}")
    
    if all_quote_code_ids:
        print(f"\nSample quote code IDs: {list(all_quote_code_ids)[:5]}")
    
    # Check for disconnection
    if quotes_with_codes == 0:
        print(f"\n>>> CRITICAL: No quotes have any codes applied!")
        print(f"   This indicates a complete disconnection between taxonomy and quotes.")
        return False
    
    if invalid_code_ids:
        print(f"\n>>> ERROR: Found {len(invalid_code_ids)} invalid code IDs")
        print(f"   These codes exist in quotes but not in taxonomy:")
        for code_id in list(invalid_code_ids)[:10]:
            print(f"   - {code_id}")
        return False
    
    # Check coverage
    codes_used = all_quote_code_ids.intersection(code_ids)
    coverage = len(codes_used) / len(code_ids) * 100 if code_ids else 0
    print(f"\nTaxonomy coverage: {coverage:.1f}% of codes are used in quotes")
    
    if coverage < 10:
        print(f">>> WARNING: Very low taxonomy coverage indicates potential issues")
    
    return quotes_with_codes > 0 and len(invalid_code_ids) == 0

if __name__ == "__main__":
    # Test multiple outputs if they exist
    test_dirs = [
        "output_performance_optimized",
        "output_performance_baseline",
        "test_output_stats",
        "test_output_full"
    ]
    
    all_passed = True
    for test_dir in test_dirs:
        if Path(test_dir).exists():
            passed = test_code_connections(test_dir)
            if not passed:
                all_passed = False
        else:
            print(f"\nSkipping {test_dir} (not found)")
    
    print(f"\n{'='*60}")
    if all_passed:
        print(">>> All tests passed!")
    else:
        print(">>> Tests failed - code connection issue confirmed")
    print(f"{'='*60}")
    
    sys.exit(0 if all_passed else 1)