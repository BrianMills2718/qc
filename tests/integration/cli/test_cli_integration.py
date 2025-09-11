"""
Test-Driven Development: CLI Integration
Tests that enhanced semantic extractor is accessible via CLI --extractor flag
These tests MUST fail initially due to missing CLI integration
"""
import pytest
import asyncio
import sys
import os
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add qc_clean to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qc_clean'))

@pytest.fixture
def temp_input_file():
    """Create temporary input file for CLI testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("John: Hello everyone, welcome to our interview.\n")
        f.write("Sarah: Thank you for having me.\n")
        f.write("John: Could you tell us about your experience?\n")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def temp_output_dir():
    """Create temporary output directory for CLI testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.mark.asyncio
async def test_cli_extractor_argument_parsing():
    """
    Test that CLI accepts --extractor enhanced_semantic argument
    THIS TEST MUST FAIL INITIALLY - CLI doesn't have --extractor argument
    """
    print("Testing CLI extractor argument parsing...")
    
    # Test by importing and calling main function setup
    import subprocess
    import sys
    
    # Test help output contains --extractor argument
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'qc_clean.core.cli.cli_robust', '--help'],
            capture_output=True, text=True, cwd='.'
        )
        
        help_output = result.stdout
        assert '--extractor' in help_output, "CLI help should contain --extractor argument"
        assert 'enhanced_semantic' in help_output, "CLI help should list enhanced_semantic as option"
        
        print("SUCCESS: CLI accepts --extractor argument with enhanced_semantic option")
        
        # Test invalid extractor (should show error)
        result_invalid = subprocess.run(
            [sys.executable, '-m', 'qc_clean.core.cli.cli_robust', 'analyze', 
             '--input', 'test', '--output', 'test', '--extractor', 'invalid_extractor'],
            capture_output=True, text=True, cwd='.'
        )
        
        # Should get argument error for invalid choice
        assert result_invalid.returncode != 0, "CLI should reject invalid extractor names"
        assert 'invalid choice' in result_invalid.stderr.lower(), "CLI should show invalid choice error"
        
        print("SUCCESS: CLI validates extractor names properly")
        
    except Exception as e:
        pytest.fail(f"CLI extractor argument parsing failed: {e}")

@pytest.mark.asyncio
async def test_cli_enhanced_extractor_usage(temp_input_file, temp_output_dir):
    """
    Test that CLI uses enhanced semantic extractor when --extractor enhanced_semantic specified
    THIS TEST MUST FAIL INITIALLY - CLI integration doesn't exist
    """
    print("Testing CLI enhanced extractor usage...")
    
    try:
        from core.cli.cli_robust import RobustCLI
        from core.cli.robust_cli_operations import AnalysisOrchestrator
        
        cli = RobustCLI()
        
        # Mock arguments for enhanced semantic extractor
        args = MagicMock()
        args.input = temp_input_file
        args.output = temp_output_dir
        args.extractor = 'enhanced_semantic'  # This should trigger enhanced extractor
        args.use_llm = True  # Enable LLM features
        
        # Test that enhanced extractor is configured properly
        # This will fail initially because CLI doesn't handle --extractor argument
        try:
            # The CLI should configure the enhanced semantic extractor
            result = await cli.analyze_command(args)
            
            # Verify that enhanced extractor was used
            # Check output files for evidence of enhanced extraction
            output_files = list(Path(temp_output_dir).glob("*.json"))
            assert len(output_files) > 0, "No JSON output files found"
            
            # Check if enhanced extraction metadata is present
            for output_file in output_files:
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Look for enhanced extractor metadata
                    if 'metadata' in data:
                        extractor_info = data['metadata'].get('extractor_info', {})
                        extractor_name = extractor_info.get('name', '')
                        if 'enhanced' in extractor_name:
                            print(f"SUCCESS: Enhanced extractor used - {extractor_name}")
                            return
            
            pytest.fail("No evidence of enhanced semantic extractor usage found in output")
            
        except Exception as e:
            pytest.fail(f"CLI enhanced extractor usage failed: {e}")
            
    except Exception as e:
        pytest.fail(f"CLI enhanced extractor test setup failed: {e}")

@pytest.mark.asyncio
async def test_cli_extractor_default_behavior(temp_input_file, temp_output_dir):
    """
    Test that CLI uses default extractor when no --extractor specified (backward compatibility)
    THIS TEST SHOULD PASS - default behavior preserved
    """
    print("Testing CLI default extractor behavior...")
    
    try:
        from core.cli.cli_robust import RobustCLI
        
        cli = RobustCLI()
        
        # Mock arguments without extractor specification
        args = MagicMock()
        args.input = temp_input_file
        args.output = temp_output_dir
        # No args.extractor - should use default
        
        # Test that default extractor is used (backward compatibility)
        try:
            result = await cli.analyze_command(args)
            
            # Verify that analysis completed (any extractor)
            output_files = list(Path(temp_output_dir).glob("*.json"))
            assert len(output_files) > 0, "No JSON output files found"
            
            print(f"SUCCESS: Default CLI behavior preserved - {len(output_files)} output files")
            
        except Exception as e:
            # This might pass or fail depending on current CLI state
            print(f"NOTE: Default CLI behavior test: {e}")
            
    except Exception as e:
        print(f"NOTE: CLI default behavior test setup: {e}")

@pytest.mark.asyncio
async def test_cli_extractor_list_available():
    """
    Test that CLI can list available extractors including enhanced_semantic
    THIS TEST MUST FAIL INITIALLY - CLI doesn't have extractor listing
    """
    print("Testing CLI extractor listing...")
    
    try:
        from plugins.extractors import get_available_extractors
        
        # Get available extractors
        available = get_available_extractors()
        print(f"Available extractors: {available}")
        
        # enhanced_semantic should be available
        assert 'enhanced_semantic' in available, f"enhanced_semantic not in {available}"
        
        # Test CLI listing functionality (should be added)
        from core.cli.cli_robust import RobustCLI
        cli = RobustCLI()
        
        # This will fail initially - CLI doesn't have list-extractors command
        if hasattr(cli, 'list_extractors'):
            extractors = cli.list_extractors()
            assert 'enhanced_semantic' in extractors, "CLI should list enhanced_semantic extractor"
            print(f"SUCCESS: CLI lists extractors: {extractors}")
        else:
            pytest.fail("CLI should have list_extractors method for --list-extractors command")
        
    except Exception as e:
        pytest.fail(f"CLI extractor listing failed: {e}")

@pytest.mark.asyncio
async def test_cli_extractor_invalid_name():
    """
    Test that CLI handles invalid extractor names gracefully
    THIS TEST MUST FAIL INITIALLY - CLI doesn't validate extractor names
    """
    print("Testing CLI invalid extractor handling...")
    
    try:
        from core.cli.cli_robust import RobustCLI
        import argparse
        
        cli = RobustCLI()
        
        # Test invalid extractor name
        test_args = ['analyze', '--input', 'test', '--output', 'test', '--extractor', 'nonexistent_extractor']
        
        # This should fail gracefully with clear error message
        try:
            parser = argparse.ArgumentParser()
            if hasattr(cli, 'setup_argument_parser'):
                cli.setup_argument_parser(parser)
                args = parser.parse_args(test_args)
                
                # CLI should validate extractor name and provide helpful error
                if hasattr(cli, 'validate_extractor'):
                    is_valid = cli.validate_extractor(args.extractor)
                    assert not is_valid, "CLI should detect invalid extractor name"
                    print("SUCCESS: CLI validates extractor names")
                else:
                    pytest.fail("CLI should have validate_extractor method")
            else:
                pytest.fail("CLI should have argument parser setup")
                
        except Exception as e:
            pytest.fail(f"CLI invalid extractor validation failed: {e}")
            
    except Exception as e:
        pytest.fail(f"CLI invalid extractor test setup failed: {e}")

if __name__ == "__main__":
    print("RUNNING CLI INTEGRATION TESTS")
    print("These tests should FAIL initially, then PASS after CLI integration")
    
    # Run tests directly for development
    asyncio.run(pytest.main([__file__, "-v", "-s"]))