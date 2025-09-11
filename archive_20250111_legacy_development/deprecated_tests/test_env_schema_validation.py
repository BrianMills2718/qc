#!/usr/bin/env python3
"""
Test suite for .env schema validation and completeness.
Validates that .env contains all required configuration parameters.
"""

import os
import sys
from pathlib import Path

def test_env_schema_completeness():
    """EVIDENCE: .env must contain all required configuration parameters"""
    
    env_file = Path('.env')
    assert env_file.exists(), ".env file must exist"
    
    env_content = env_file.read_text()
    
    required_settings = [
        # Core API settings
        'API_KEY', 'MODEL', 'API_PROVIDER',
        # Research methodology
        'METHODOLOGY', 'CODING_APPROACH', 'CODING_DEPTH', 'THEORETICAL_SENSITIVITY',
        # LLM parameters
        'TEMPERATURE', 'CONFIDENCE_THRESHOLD', 'MAX_TOKENS',
        # Analysis settings
        'VALIDATION_LEVEL', 'MINIMUM_CODE_FREQUENCY', 'MEMO_GENERATION_FREQUENCY',
        # Quality control
        'MINIMUM_CONFIDENCE', 'RELATIONSHIP_CONFIDENCE_THRESHOLD',
        # Output parameters
        'INCLUDE_SUPPORTING_QUOTES', 'INCLUDE_AUDIT_TRAIL',
        # Extractor configuration
        'EXTRACTOR_TYPE'
    ]
    
    missing = []
    for setting in required_settings:
        if setting not in env_content:
            missing.append(setting)
    
    assert not missing, f"Missing required .env settings: {missing}"
    print("PASS: All required .env settings present")
    return True

def test_env_backward_compatibility():
    """EVIDENCE: Existing API keys must continue working"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Backup existing keys
    existing_keys = {}
    key_vars = ['OPENAI_API_KEY', 'GEMINI_API_KEY', 'ANTHROPIC_API_KEY']
    for var in key_vars:
        if var in os.environ:
            existing_keys[var] = os.environ[var]
    
    assert len(existing_keys) > 0, "At least one API key must be configured"
    
    # Test that keys are valid format (basic validation)
    for key, value in existing_keys.items():
        if key == 'OPENAI_API_KEY':
            assert value.startswith('sk-'), f"Invalid OpenAI API key format for {key}"
        elif key == 'GEMINI_API_KEY':
            assert value.startswith('AIza'), f"Invalid Gemini API key format for {key}"
        elif key == 'ANTHROPIC_API_KEY':
            assert value.startswith('sk-ant-'), f"Invalid Anthropic API key format for {key}"
    
    print("PASS: API keys are properly formatted")
    return True

def test_env_configuration_values():
    """EVIDENCE: Configuration values must be valid"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test methodology values
    methodology = os.getenv('METHODOLOGY', '')
    valid_methodologies = ['grounded_theory', 'thematic_analysis', 'phenomenological', 'critical_theory', 'constructivist']
    assert methodology in valid_methodologies, f"Invalid METHODOLOGY: {methodology}. Valid options: {valid_methodologies}"
    
    # Test coding approach values
    coding_approach = os.getenv('CODING_APPROACH', '')
    valid_approaches = ['open', 'closed', 'mixed']
    assert coding_approach in valid_approaches, f"Invalid CODING_APPROACH: {coding_approach}. Valid options: {valid_approaches}"
    
    # Test validation level values
    validation_level = os.getenv('VALIDATION_LEVEL', '')
    valid_levels = ['minimal', 'standard', 'rigorous']
    assert validation_level in valid_levels, f"Invalid VALIDATION_LEVEL: {validation_level}. Valid options: {valid_levels}"
    
    # Test temperature range
    temperature = float(os.getenv('TEMPERATURE', '0.1'))
    assert 0.0 <= temperature <= 2.0, f"Invalid TEMPERATURE: {temperature}. Must be 0.0-2.0"
    
    # Test confidence thresholds
    confidence = float(os.getenv('CONFIDENCE_THRESHOLD', '0.6'))
    assert 0.0 <= confidence <= 1.0, f"Invalid CONFIDENCE_THRESHOLD: {confidence}. Must be 0.0-1.0"
    
    min_confidence = float(os.getenv('MINIMUM_CONFIDENCE', '0.3'))
    assert 0.0 <= min_confidence <= 1.0, f"Invalid MINIMUM_CONFIDENCE: {min_confidence}. Must be 0.0-1.0"
    
    print("PASS: All configuration values are valid")
    return True

if __name__ == '__main__':
    print("Testing .env schema validation...")
    
    try:
        test_env_schema_completeness()
        test_env_backward_compatibility()
        test_env_configuration_values()
        print("\nALL TESTS PASSED: .env schema is complete and valid")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)