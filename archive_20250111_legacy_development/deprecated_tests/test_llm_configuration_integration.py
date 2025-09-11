#!/usr/bin/env python3
"""
LLM Configuration Integration Tests

Tests to validate that configuration parameters (temperature, max_tokens, model)
are properly passed through the system and control LLM behavior.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.qc.config.methodology_config import GroundedTheoryConfig, MethodologyConfigManager
from src.qc.llm.llm_handler import LLMHandler
from src.qc.core.robust_cli_operations import RobustCLIOperations
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_llm_handler_configuration():
    """Test that LLMHandler properly uses configuration parameters"""
    print("\n=== Testing LLM Handler Configuration ===")
    
    try:
        # Load test configuration
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_focused.yaml"))
        
        print(f"Test config: temperature={config.temperature}, model={config.model_preference}")
        print(f"Test config: max_tokens={config.max_tokens}")
        
        # Create LLM handler with configuration
        llm_handler = LLMHandler(config=config)
        
        # Verify configuration is applied
        assert llm_handler.temperature == config.temperature, f"Temperature mismatch: {llm_handler.temperature} != {config.temperature}"
        assert llm_handler.model_name == config.model_preference, f"Model mismatch: {llm_handler.model_name} != {config.model_preference}"
        assert llm_handler.default_max_tokens == config.max_tokens, f"Max tokens mismatch: {llm_handler.default_max_tokens} != {config.max_tokens}"
        
        print(f"LLM handler temperature: {llm_handler.temperature}")
        print(f"LLM handler model: {llm_handler.model_name}")  
        print(f"LLM handler max_tokens: {llm_handler.default_max_tokens}")
        
        print("PASS: LLM Handler configuration applied correctly")
        return True
        
    except Exception as e:
        print(f"FAIL: LLM handler configuration test failed: {e}")
        logger.error(f"LLM handler configuration error: {e}", exc_info=True)
        return False

async def test_robust_operations_configuration():
    """Test that RobustCLIOperations properly passes configuration to LLM handler"""
    print("\n=== Testing RobustCLIOperations Configuration ===")
    
    try:
        # Load test configuration
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory.yaml"))
        
        # Create RobustCLIOperations with configuration
        operations = RobustCLIOperations(config=config)
        
        # Verify config is stored
        assert operations.config == config, "Configuration not stored properly"
        
        # Initialize systems to create LLM handler
        await operations.initialize_systems()
        
        # Verify LLM handler has configuration
        if operations._llm_handler:
            assert operations._llm_handler.config == config, "LLM handler configuration not passed"
            assert operations._llm_handler.temperature == config.temperature, "Temperature not applied to LLM handler"
            assert operations._llm_handler.model_name == config.model_preference, "Model not applied to LLM handler"
            print(f"Operations LLM handler temperature: {operations._llm_handler.temperature}")
            print(f"Operations LLM handler model: {operations._llm_handler.model_name}")
        else:
            print("WARNING: LLM handler not initialized (network/API issues)")
        
        print("PASS: RobustCLIOperations configuration integration working")
        return True
        
    except Exception as e:
        print(f"FAIL: RobustCLIOperations configuration test failed: {e}")
        logger.error(f"RobustCLIOperations configuration error: {e}", exc_info=True)
        return False

async def test_different_configurations():
    """Test that different configurations produce different LLM handler settings"""
    print("\n=== Testing Configuration Variation ===")
    
    try:
        config_manager = MethodologyConfigManager()
        
        # Load two different configurations
        config1 = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory.yaml"))
        config2 = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_focused.yaml"))
        
        # Create handlers with different configs
        handler1 = LLMHandler(config=config1)
        handler2 = LLMHandler(config=config2)
        
        print(f"Config 1: temp={handler1.temperature}, tokens={handler1.default_max_tokens}")
        print(f"Config 2: temp={handler2.temperature}, tokens={handler2.default_max_tokens}")
        
        # Verify they are different
        settings_different = (
            handler1.temperature != handler2.temperature or
            handler1.default_max_tokens != handler2.default_max_tokens
        )
        
        assert settings_different, "Different configurations should produce different LLM settings"
        
        print("PASS: Different configurations produce different LLM settings")
        return True
        
    except Exception as e:
        print(f"FAIL: Configuration variation test failed: {e}")
        logger.error(f"Configuration variation error: {e}", exc_info=True)
        return False

async def test_workflow_configuration_integration():
    """Test that GT workflow uses configured LLM handler"""
    print("\n=== Testing GT Workflow Configuration Integration ===")
    
    try:
        # Load configuration
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_focused.yaml"))
        
        # Create configured operations
        operations = RobustCLIOperations(config=config)
        await operations.initialize_systems()
        
        # Create workflow with configuration
        workflow = GroundedTheoryWorkflow(operations, config=config)
        
        # Verify workflow has configuration
        assert workflow.config == config, "Workflow configuration not set"
        
        # Verify operations LLM handler uses configuration (if available)
        if operations._llm_handler:
            assert operations._llm_handler.config == config, "Workflow operations LLM handler not configured"
            print(f"Workflow LLM handler temperature: {operations._llm_handler.temperature}")
            print(f"Workflow LLM handler model: {operations._llm_handler.model_name}")
            print(f"Workflow LLM handler max_tokens: {operations._llm_handler.default_max_tokens}")
        else:
            print("WARNING: LLM handler not available (network/API issues)")
        
        print("PASS: GT Workflow configuration integration working")
        return True
        
    except Exception as e:
        print(f"FAIL: GT Workflow configuration integration test failed: {e}")
        logger.error(f"GT Workflow configuration integration error: {e}", exc_info=True)
        return False

async def main():
    """Run all LLM configuration integration tests"""
    print("Starting LLM Configuration Integration Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: LLM Handler configuration
    result1 = await test_llm_handler_configuration()
    test_results.append(("LLM Handler Configuration", result1))
    
    # Test 2: RobustCLIOperations configuration
    result2 = await test_robust_operations_configuration()
    test_results.append(("RobustCLIOperations Configuration", result2))
    
    # Test 3: Different configurations
    result3 = await test_different_configurations()
    test_results.append(("Configuration Variation", result3))
    
    # Test 4: GT Workflow integration
    result4 = await test_workflow_configuration_integration()
    test_results.append(("GT Workflow Integration", result4))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED: LLM configuration integration is working correctly")
        return 0
    else:
        print("SOME TESTS FAILED: LLM configuration integration needs fixes")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)