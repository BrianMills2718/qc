import asyncio
import json
from pathlib import Path
from datetime import datetime
import logging

# Configure detailed logging to track retry attempts
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_reliability_with_complex_interviews():
    """Test LLM reliability improvements with actual research data"""
    
    print("=== LLM Reliability Test with Complex Research Data ===")
    
    # Load reliable configuration
    from src.qc.config.methodology_config import MethodologyConfigManager
    config_manager = MethodologyConfigManager()
    config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_reliable.yaml"))
    
    # Initialize system with retry-enabled LLM handler
    from src.qc.core.robust_cli_operations import RobustCLIOperations
    operations = RobustCLIOperations(config=config)
    await operations.initialize_systems()
    
    # Load the exact interview data that was failing (6K-54K chars)
    interviews = operations.robust_load_interviews(Path("data/interviews/ai_interviews_3_for_test"))
    
    print(f"Loaded {len(interviews)} interviews")
    for i, interview in enumerate(interviews):
        text_length = len(interview.get('text', ''))
        print(f"  Interview {i+1}: {text_length} characters")
    
    # Test open coding phase which was returning NULL responses
    from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
    workflow = GroundedTheoryWorkflow(operations, config=config)
    
    print(f"\n=== Testing Open Coding Phase with Retry Logic ===")
    start_time = datetime.now()
    
    try:
        # This should now work with retry logic even if Gemini returns 500 errors
        open_codes = await workflow._open_coding_phase(interviews)
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"RESULT: Generated {len(open_codes) if open_codes else 0} codes in {duration:.1f}s")
        
        if open_codes and len(open_codes) > 0:
            print("SUCCESS: Open coding with retry logic works!")
            for i, code in enumerate(open_codes[:5]):  # Show first 5 codes
                print(f"  Code {i+1}: {code.code_name} (freq={code.frequency}, conf={code.confidence:.2f})")
            
            # Test axial coding phase
            print(f"\n=== Testing Axial Coding Phase ===")
            axial_start = datetime.now()
            
            try:
                relationships = await workflow._axial_coding_phase(open_codes, interviews)
                axial_duration = (datetime.now() - axial_start).total_seconds()
                
                print(f"RESULT: Generated {len(relationships) if relationships else 0} relationships in {axial_duration:.1f}s")
                
                if relationships and len(relationships) > 0:
                    print("SUCCESS: Axial coding also works with retry logic!")
                    for i, rel in enumerate(relationships[:3]):
                        print(f"  Rel {i+1}: {rel.central_category} → {rel.related_category} (strength={rel.strength:.2f})")
                else:
                    print("INFO: Axial coding generated 0 relationships (may be normal for some data)")
                
                return True
                
            except Exception as e:
                print(f"FAILED: Axial coding failed: {e}")
                return False
        else:
            print("FAILED: Open coding still returns 0 codes even with retry logic")
            return False
            
    except Exception as e:
        print(f"FAILED: Open coding phase failed even with retry logic: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_simulation():
    """Simulate server errors to validate retry mechanisms"""
    
    print(f"\n=== Error Simulation Test ===")
    
    # This would require mocking litellm to return controlled errors
    # Implementation depends on the actual retry logic structure
    print("Note: Error simulation requires mock framework integration")
    print("Manual testing: Monitor logs during complex data processing")

async def test_configuration_loading():
    """Test that the new configuration loads properly"""
    
    print(f"\n=== Configuration Loading Test ===")
    
    try:
        from src.qc.config.methodology_config import MethodologyConfigManager
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_reliable.yaml"))
        
        print("SUCCESS: Configuration loaded successfully")
        print(f"  Model: {config.model_preference}")
        print(f"  Max tokens: {config.max_tokens}")
        print(f"  Temperature: {config.temperature}")
        print(f"  Max retries: {config.max_llm_retries}")
        print(f"  Base delay: {config.base_retry_delay}")
        print(f"  Circuit breaker threshold: {config.circuit_breaker_threshold}")
        print(f"  Request timeout: {config.request_timeout}")
        return True
        
    except Exception as e:
        print(f"FAILED: Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_llm_handler_initialization():
    """Test that LLMHandler initializes with retry parameters"""
    
    print(f"\n=== LLM Handler Initialization Test ===")
    
    try:
        from src.qc.config.methodology_config import MethodologyConfigManager
        from src.qc.llm.llm_handler import LLMHandler
        
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_reliable.yaml"))
        
        # Initialize LLM handler with config
        llm_handler = LLMHandler(config=config)
        
        print("SUCCESS: LLM Handler initialized with retry logic")
        print(f"  Max retries: {llm_handler.max_retries}")
        print(f"  Base delay: {llm_handler.base_delay}")
        print(f"  Circuit breaker threshold: {llm_handler.circuit_breaker_threshold}")
        print(f"  Circuit breaker timeout: {llm_handler.circuit_breaker_timeout}")
        
        # Test retry methods exist
        assert hasattr(llm_handler, '_calculate_backoff_delay'), "Missing _calculate_backoff_delay method"
        assert hasattr(llm_handler, '_is_retryable_error'), "Missing _is_retryable_error method"
        assert hasattr(llm_handler, '_retry_with_backoff'), "Missing _retry_with_backoff method"
        
        # Test backoff calculation
        delay_0 = llm_handler._calculate_backoff_delay(0)
        delay_1 = llm_handler._calculate_backoff_delay(1)
        print(f"  Backoff delays: attempt 0 = {delay_0:.2f}s, attempt 1 = {delay_1:.2f}s")
        
        # Test retryable error detection
        retryable = llm_handler._is_retryable_error(Exception("HTTP 500: Internal Server Error"))
        non_retryable = llm_handler._is_retryable_error(Exception("Invalid API key"))
        print(f"  Error classification: 500 error = {retryable}, API key error = {non_retryable}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: LLM Handler initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def run_all_tests():
        print("Starting LLM Reliability Test Suite")
        print("=" * 60)
        
        # Test 1: Configuration loading
        config_success = await test_configuration_loading()
        
        # Test 2: LLM Handler initialization
        handler_success = await test_llm_handler_initialization()
        
        # Test 3: Reliability with complex interviews (if config and handler work)
        reliability_success = False
        if config_success and handler_success:
            reliability_success = await test_reliability_with_complex_interviews()
        else:
            print("\nSKIPPING reliability test due to configuration/handler failures")
        
        # Test 4: Error simulation
        await test_error_simulation()
        
        print(f"\n{'='*60}")
        print(f"Test Results Summary:")
        print(f"  Configuration Loading: {'SUCCESS' if config_success else 'FAILED'}")
        print(f"  LLM Handler Init: {'SUCCESS' if handler_success else 'FAILED'}")
        print(f"  Reliability Test: {'SUCCESS' if reliability_success else 'FAILED'}")
        
        overall_success = config_success and handler_success and reliability_success
        print(f"  Overall Result: {'SUCCESS' if overall_success else 'FAILED'}")
        
        return overall_success
    
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)