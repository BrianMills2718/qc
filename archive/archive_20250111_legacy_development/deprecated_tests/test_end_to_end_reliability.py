import asyncio
import pytest
from pathlib import Path
from datetime import datetime
import logging

# Configure comprehensive logging for end-to-end testing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TestEndToEndReliability:
    """Comprehensive end-to-end reliability tests for GT workflow with retry logic"""
    
    @pytest.mark.asyncio
    async def test_complete_gt_workflow_with_retries(self):
        """Test complete GT workflow with retry-enabled LLM handler"""
        
        print("=== Complete GT Workflow Reliability Test ===")
        
        # Load reliable configuration
        from src.qc.config.methodology_config import MethodologyConfigManager
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_reliable.yaml"))
        
        # Initialize system
        from src.qc.core.robust_cli_operations import RobustCLIOperations
        operations = RobustCLIOperations(config=config)
        init_success = await operations.initialize_systems()
        
        assert init_success, "System initialization should succeed"
        
        # Load complex interview data (the data that previously failed)
        interviews = operations.robust_load_interviews(Path("data/interviews/ai_interviews_3_for_test"))
        assert len(interviews) > 0, "Should load interview data"
        
        # Verify we have complex interviews (6K-54K chars)
        total_chars = sum(len(interview.get('text', '')) for interview in interviews)
        print(f"Total interview text: {total_chars} characters")
        assert total_chars > 5000, "Should have substantial interview content"
        
        # Initialize workflow
        from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
        workflow = GroundedTheoryWorkflow(operations, config=config)
        
        # Test Phase 1: Open Coding (this was failing with NULL responses)
        print("\n--- Phase 1: Open Coding ---")
        start_time = datetime.now()
        
        open_codes = await workflow._open_coding_phase(interviews)
        phase1_duration = (datetime.now() - start_time).total_seconds()
        
        # Assertions for open coding success
        assert open_codes is not None, "Open coding should not return None"
        assert isinstance(open_codes, list), "Open codes should be a list"
        assert len(open_codes) > 0, "Should generate at least 1 code with reliable configuration"
        
        print(f"SUCCESS: Open coding successful: {len(open_codes)} codes in {phase1_duration:.1f}s")
        for i, code in enumerate(open_codes[:3]):
            print(f"  Code {i+1}: {code.code_name} (freq={code.frequency})")
        
        # Test Phase 2: Axial Coding
        print("\n--- Phase 2: Axial Coding ---")
        start_time = datetime.now()
        
        relationships = await workflow._axial_coding_phase(open_codes, interviews)
        phase2_duration = (datetime.now() - start_time).total_seconds()
        
        # Assertions for axial coding
        assert relationships is not None, "Axial coding should not return None"
        assert isinstance(relationships, list), "Relationships should be a list"
        
        print(f"SUCCESS: Axial coding successful: {len(relationships)} relationships in {phase2_duration:.1f}s")
        if relationships:
            for i, rel in enumerate(relationships[:2]):
                print(f"  Relationship {i+1}: {rel.central_category} → {rel.related_category}")
        
        # Test Phase 3: Selective Coding
        print("\n--- Phase 3: Selective Coding ---")
        start_time = datetime.now()
        
        theoretical_model = await workflow._selective_coding_phase(open_codes, relationships, interviews)
        phase3_duration = (datetime.now() - start_time).total_seconds()
        
        # Assertions for selective coding
        assert theoretical_model is not None, "Selective coding should not return None"
        
        print(f"SUCCESS: Selective coding successful: {theoretical_model.model_name} in {phase3_duration:.1f}s")
        print(f"  Core category: {theoretical_model.core_category}")
        
        # Overall success metrics
        total_duration = phase1_duration + phase2_duration + phase3_duration
        print(f"\n=== Overall Success Metrics ===")
        print(f"Total processing time: {total_duration:.1f}s")
        print(f"Codes generated: {len(open_codes)}")
        print(f"Relationships generated: {len(relationships)}")
        print(f"Theoretical model: {theoretical_model.model_name}")
        
        # Verify success criteria
        assert total_duration < 300, "Should complete within 5 minutes"  # 5 minutes max
        assert len(open_codes) >= 1, "Should generate at least 1 code"
        assert theoretical_model.model_name, "Should generate a named theoretical model"
        
        print("SUCCESS: END-TO-END TEST PASSED: Complete GT workflow successful with retry logic")
        return True
    
    @pytest.mark.asyncio
    async def test_retry_logic_under_load(self):
        """Test retry logic behavior with multiple concurrent requests"""
        
        print("\n=== Retry Logic Load Test ===")
        
        from src.qc.config.methodology_config import MethodologyConfigManager
        from src.qc.llm.llm_handler import LLMHandler
        # Use simple schema to avoid import issues
        from pydantic import BaseModel
        from typing import List
        
        class SimpleTestResponse(BaseModel):
            message: str
            value: int
        
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_reliable.yaml"))
        
        # Create multiple LLM handler instances
        handlers = [LLMHandler(config=config) for _ in range(3)]
        
        # Simple prompt for testing
        test_prompt = "Generate a simple test response with message 'Test successful' and value 42."
        
        async def make_request(handler_id, handler):
            """Make a single request with retry logic"""
            try:
                result = await handler.extract_structured(
                    prompt=test_prompt,
                    schema=SimpleTestResponse,
                    max_tokens=1000
                )
                print(f"  Handler {handler_id}: SUCCESS - {result.message}")
                return True
            except Exception as e:
                print(f"  Handler {handler_id}: FAILED - {e}")
                return False
        
        # Run multiple concurrent requests
        print("Running 3 concurrent requests...")
        start_time = datetime.now()
        
        tasks = [make_request(i, handler) for i, handler in enumerate(handlers)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        load_duration = (datetime.now() - start_time).total_seconds()
        
        # Analyze results
        successful_requests = sum(1 for r in results if r is True)
        print(f"Load test results: {successful_requests}/3 requests successful in {load_duration:.1f}s")
        
        # Should have at least 2/3 success rate
        assert successful_requests >= 2, f"Should have at least 2/3 successful requests, got {successful_requests}/3"
        
        print("SUCCESS: LOAD TEST PASSED: Retry logic handles concurrent requests")
        return True
    
    @pytest.mark.asyncio 
    async def test_circuit_breaker_functionality(self):
        """Test that circuit breaker prevents cascade failures"""
        
        print("\n=== Circuit Breaker Test ===")
        
        from src.qc.config.methodology_config import MethodologyConfigManager
        from src.qc.llm.llm_handler import LLMHandler
        
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_reliable.yaml"))
        
        handler = LLMHandler(config=config)
        
        # Verify circuit breaker state management exists
        assert hasattr(handler, 'failure_count'), "Handler should have failure_count attribute"
        assert hasattr(handler, 'circuit_breaker_threshold'), "Handler should have circuit breaker threshold"
        assert hasattr(handler, '_should_circuit_break'), "Handler should have circuit breaker check method"
        assert hasattr(handler, '_record_failure'), "Handler should have failure recording method"
        assert hasattr(handler, '_record_success'), "Handler should have success recording method"
        
        # Test initial state
        assert handler.failure_count == 0, "Initial failure count should be 0"
        assert not handler._should_circuit_break(), "Circuit breaker should be closed initially"
        
        # Simulate failures to test circuit breaker
        for i in range(handler.circuit_breaker_threshold):
            handler._record_failure()
        
        print(f"Recorded {handler.circuit_breaker_threshold} failures")
        assert handler.failure_count == handler.circuit_breaker_threshold, "Failure count should match threshold"
        assert handler._should_circuit_break(), "Circuit breaker should be open after threshold failures"
        
        # Test recovery
        handler._record_success()
        assert handler.failure_count == 0, "Success should reset failure count"
        assert not handler._should_circuit_break(), "Circuit breaker should close after success"
        
        print("SUCCESS: CIRCUIT BREAKER TEST PASSED: Proper failure tracking and recovery")
        return True

# Standalone test runner for manual execution
async def run_end_to_end_tests():
    """Run all end-to-end reliability tests"""
    
    print("Starting End-to-End Reliability Test Suite")
    print("=" * 60)
    
    test_instance = TestEndToEndReliability()
    
    results = {}
    
    # Test 1: Complete GT workflow
    try:
        results['complete_workflow'] = await test_instance.test_complete_gt_workflow_with_retries()
    except Exception as e:
        print(f"FAILED: Complete workflow test failed: {e}")
        results['complete_workflow'] = False
    
    # Test 2: Retry logic under load
    try:
        results['load_test'] = await test_instance.test_retry_logic_under_load()
    except Exception as e:
        print(f"FAILED: Load test failed: {e}")
        results['load_test'] = False
    
    # Test 3: Circuit breaker functionality
    try:
        results['circuit_breaker'] = await test_instance.test_circuit_breaker_functionality()
    except Exception as e:
        print(f"FAILED: Circuit breaker test failed: {e}")
        results['circuit_breaker'] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("End-to-End Test Results:")
    for test_name, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"  {test_name}: {status}")
    
    overall_success = all(results.values())
    print(f"\nOverall Result: {'SUCCESS' if overall_success else 'FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(run_end_to_end_tests())
    exit(0 if success else 1)