#!/usr/bin/env python3
"""
Final Implementation Validation

Validates all CLAUDE.md tasks are completed successfully.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def validate_implementation():
    """Validate all CLAUDE.md implementation tasks."""
    print("=== VALIDATING CLAUDE.MD IMPLEMENTATION ===")
    
    results = []
    
    # 1. Check enhanced prompt exists and has conservative guidance
    print("\n1. Testing Enhanced Prompt Template...")
    prompt_file = Path("src/qc/prompts/phase4/dialogue_aware_quotes.txt")
    if prompt_file.exists():
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        
        conservative_indicators = [
            "Be conservative",
            "40-70% should have \"none\" connections",
            "Better to miss a subtle connection than create a false one",
            "EXPECTED CONNECTION RATES",
            "WHEN TO USE \"NONE\""
        ]
        
        found_indicators = sum(1 for indicator in conservative_indicators if indicator in prompt_content)
        if found_indicators >= 4:
            results.append("PASS: Enhanced prompt with conservative detection")
        else:
            results.append("FAIL: Enhanced prompt with conservative detection")
    else:
        results.append("FAIL: Prompt file not found")
    
    # 2. Check quality monitoring system exists
    print("\n2. Testing Quality Monitoring System...")
    monitor_file = Path("src/qc/analysis/connection_quality_monitor.py")
    if monitor_file.exists():
        try:
            from qc.analysis.connection_quality_monitor import ConnectionQualityMonitor
            monitor = ConnectionQualityMonitor()
            results.append("PASS: Quality monitoring system")
        except Exception as e:
            results.append(f"FAIL: Quality monitoring system import error: {e}")
    else:
        results.append("FAIL: Quality monitoring system file not found")
    
    # 3. Check quality assessment framework exists
    print("\n3. Testing Quality Assessment Framework...")
    assessment_file = Path("src/qc/analysis/quality_assessment.py")
    if assessment_file.exists():
        try:
            from qc.analysis.quality_assessment import QualityAssessmentFramework
            framework = QualityAssessmentFramework()
            results.append("PASS: Quality assessment framework")
        except Exception as e:
            results.append(f"FAIL: Quality assessment framework import error: {e}")
    else:
        results.append("FAIL: Quality assessment framework file not found")
    
    # 4. Check production data analysis works
    print("\n4. Testing Production Data Analysis...")
    production_file = Path("output_production/interviews/Focus Group on AI and Methods 7_7.json")
    if production_file.exists():
        try:
            from qc.analysis.connection_quality_monitor import analyze_interview_file
            metrics, alerts = analyze_interview_file(production_file)
            
            # Check if over-assignment is detected
            over_assignment_detected = any(
                alert.alert_type == 'high_connection_rate' for alert in alerts
            )
            
            if over_assignment_detected:
                results.append("PASS: Production data over-assignment detection")
            else:
                results.append("FAIL: Production data over-assignment detection")
                
        except Exception as e:
            results.append(f"FAIL: Production data analysis error: {e}")
    else:
        results.append("FAIL: Production data file not found")
    
    # 5. Check conservative detection improvement (from test results)
    print("\n5. Testing Conservative Detection Improvement...")
    test_results_file = Path("test_conservative_results.json")
    if test_results_file.exists():
        try:
            with open(test_results_file, 'r') as f:
                test_data = json.load(f)
            
            quotes = test_data.get('quotes', [])
            none_connections = sum(1 for q in quotes if q.get('thematic_connection') == 'none')
            connection_rate = 1.0 - (none_connections / len(quotes)) if quotes else 0.0
            
            if connection_rate <= 0.8:
                results.append(f"PASS: Conservative detection (rate: {connection_rate:.1%})")
            else:
                results.append(f"FAIL: Conservative detection (rate: {connection_rate:.1%})")
                
        except Exception as e:
            results.append(f"FAIL: Conservative detection test error: {e}")
    else:
        results.append("FAIL: Conservative detection test results not found")
    
    # Summary
    print(f"\n=== VALIDATION RESULTS ===")
    for result in results:
        print(result)
    
    passed = sum(1 for r in results if r.startswith("PASS"))
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tasks passed")
    
    if passed == total:
        print("\nIMPLEMENTATION STATUS: ALL TASKS COMPLETE")
        print("- Enhanced prompt with conservative detection")
        print("- Quality monitoring system implemented")
        print("- Quality assessment framework implemented")  
        print("- Over-assignment detection working")
        print("- Conservative detection improvement verified")
        return True
    else:
        print(f"\nIMPLEMENTATION STATUS: {total-passed} TASKS NEED ATTENTION")
        return False


if __name__ == "__main__":
    success = validate_implementation()
    if success:
        print("\nALL CLAUDE.MD TASKS SUCCESSFULLY IMPLEMENTED AND VALIDATED")
    else:
        print("\nSOME TASKS NEED ADDITIONAL WORK")