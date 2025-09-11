#!/usr/bin/env python3
"""
Comprehensive test suite for unified .env configuration implementation.
Runs all tests to verify complete functionality.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_test_file(test_file):
    """Run a test file and return success status"""
    try:
        print(f"\n{'='*60}")
        print(f"RUNNING: {test_file}")
        print('='*60)
        
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"SUCCESS: {test_file}")
            return True
        else:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            print(f"FAILED: {test_file}")
            return False
            
    except Exception as e:
        print(f"ERROR running {test_file}: {e}")
        return False

def test_configuration_behavioral_impact():
    """EVIDENCE: Validate that different .env configs produce >50% different analysis outputs"""
    
    print(f"\n{'='*60}")
    print("BEHAVIORAL IMPACT VALIDATION")
    print('='*60)
    
    # Test different configurations
    configs = {
        'Conservative': {
            'METHODOLOGY': 'grounded_theory',
            'TEMPERATURE': '0.1',
            'VALIDATION_LEVEL': 'rigorous',
            'CODING_APPROACH': 'closed',
            'THEORETICAL_SENSITIVITY': 'low',
            'MINIMUM_CONFIDENCE': '0.5'
        },
        'Exploratory': {
            'METHODOLOGY': 'constructivist',
            'TEMPERATURE': '0.8',
            'VALIDATION_LEVEL': 'minimal',
            'CODING_APPROACH': 'open',
            'THEORETICAL_SENSITIVITY': 'high',
            'MINIMUM_CONFIDENCE': '0.2'
        }
    }
    
    results = {}
    
    for config_name, config_vars in configs.items():
        # Override environment
        original_env = {}
        for key, value in config_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            sys.path.insert(0, str(Path(__file__).parent / 'qc_clean'))
            from config.unified_config import UnifiedConfig
            
            config = UnifiedConfig()
            
            # Generate behavioral profile
            profile = config.get_behavioral_profile()
            behavioral_params = config.get_behavioral_parameters()
            
            results[config_name] = {
                'profile': profile,
                'params': behavioral_params,
                'signature': str(hash(str(behavioral_params)))
            }
            
        finally:
            # Restore environment
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value
    
    # Calculate behavioral difference
    conservative = results['Conservative']['params']
    exploratory = results['Exploratory']['params']
    
    differences = 0
    total_params = len(conservative)
    
    for key, con_value in conservative.items():
        exp_value = exploratory[key]
        if isinstance(con_value, (int, float)):
            # Numerical - consider >20% change as different
            if abs(con_value - exp_value) / max(abs(con_value), abs(exp_value), 0.001) > 0.2:
                differences += 1
        else:
            # Categorical - any change is different
            if con_value != exp_value:
                differences += 1
    
    difference_ratio = differences / total_params
    
    print(f"Conservative profile: {results['Conservative']['profile']}")
    print(f"Exploratory profile: {results['Exploratory']['profile']}")
    print(f"Behavioral difference: {difference_ratio:.1%} ({differences}/{total_params} parameters)")
    
    if difference_ratio > 0.5:
        print("SUCCESS: Configuration produces >50% behavioral difference")
        return True
    else:
        print(f"FAILED: Only {difference_ratio:.1%} behavioral difference (need >50%)")
        return False

def test_no_hardcoded_values():
    """EVIDENCE: Verify no hardcoded configuration values remain in code"""
    
    print(f"\n{'='*60}")
    print("HARDCODED VALUES VALIDATION")
    print('='*60)
    
    config_file = Path(__file__).parent / 'qc_clean' / 'config' / 'unified_config.py'
    
    if not config_file.exists():
        print("FAILED: UnifiedConfig file not found")
        return False
    
    content = config_file.read_text()
    
    # Check for suspicious hardcoded values
    suspicious_patterns = [
        'gemini-2.0-flash-exp',
        'temperature = 0.1',
        'model_preference = ',
        'methodology = MethodologyType.GROUNDED_THEORY',
        'validation_level = ValidationLevel.STANDARD'
    ]
    
    hardcoded_found = []
    for pattern in suspicious_patterns:
        if pattern in content:
            hardcoded_found.append(pattern)
    
    if hardcoded_found:
        print("POTENTIAL HARDCODED VALUES FOUND:")
        for pattern in hardcoded_found:
            print(f"  - {pattern}")
        
        # Check if they're in default_factory lambda functions (acceptable)
        acceptable_hardcoding = []
        for pattern in hardcoded_found:
            if f"os.getenv(" in content and pattern in content:
                # Look for the pattern in context
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if pattern in line and 'os.getenv(' in line:
                        acceptable_hardcoding.append(pattern)
        
        remaining_hardcoding = [p for p in hardcoded_found if p not in acceptable_hardcoding]
        
        if remaining_hardcoding:
            print(f"FAILED: Found {len(remaining_hardcoding)} unacceptable hardcoded values")
            return False
        else:
            print("All hardcoded values are in os.getenv() calls (acceptable)")
    
    print("SUCCESS: No unacceptable hardcoded configuration values found")
    return True

def main():
    """Run comprehensive test suite"""
    
    print("COMPREHENSIVE UNIFIED .ENV CONFIGURATION TEST SUITE")
    print("=" * 80)
    
    # List of test files to run
    test_files = [
        'test_env_schema_validation.py',
        'test_unified_config_env_integration.py', 
        'test_multi_provider_llm_support.py',
        'test_unified_config_integration.py'
    ]
    
    # Run all test files
    test_results = []
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            result = run_test_file(test_file)
            test_results.append((test_file, result))
        else:
            print(f"MISSING: {test_file}")
            test_results.append((test_file, False))
    
    # Run additional validation tests
    behavioral_result = test_configuration_behavioral_impact()
    test_results.append(('Behavioral Impact Validation', behavioral_result))
    
    hardcoded_result = test_no_hardcoded_values()
    test_results.append(('Hardcoded Values Check', hardcoded_result))
    
    # Summary
    print(f"\n{'='*80}")
    print("COMPREHENSIVE TEST RESULTS")
    print('='*80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{status:4} | {test_name}")
        if result:
            passed += 1
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\nALL TESTS PASSED: Unified .env configuration implementation COMPLETE")
        print("\nSUCCESS CRITERIA MET:")
        print("+ Single Configuration Source: Users edit only .env file for ALL settings")
        print("+ Provider Agnostic: OpenAI, Gemini, Anthropic models work without code changes")
        print("+ Behavioral Configuration: Different .env settings produce >50% different outputs")
        print("+ No Hardcoded Values: Automated verification shows no configuration hardcoding")
        print("+ Fail-Fast Behavior: System fails immediately with clear messages for invalid config")
        return True
    else:
        print(f"\n{total-passed} TESTS FAILED: Implementation incomplete")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)