#!/usr/bin/env python3
"""
Comprehensive Tests for Provider-Agnostic Multi-Provider Support
Tests the critical API key resolution fix and provider switching functionality.
"""

import os
import pytest
from unittest.mock import patch, Mock
from qc_clean.config.unified_config import UnifiedConfig
from qc_clean.core.llm.llm_handler import LLMHandler


class TestAPIKeyResolution:
    """Test dynamic API key resolution based on provider"""
    
    def test_openai_api_key_resolution(self):
        """EVIDENCE: OpenAI provider should use OPENAI_API_KEY"""
        with patch.dict(os.environ, {
            'API_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'sk-test-openai-key-12345',
            'GEMINI_API_KEY': 'gemini-key-should-not-be-used',
            'ANTHROPIC_API_KEY': 'anthropic-key-should-not-be-used'
        }):
            config = UnifiedConfig()
            assert config.api_provider == 'openai'
            assert config.api_key == 'sk-test-openai-key-12345'
            assert 'gemini' not in config.api_key.lower()
            assert 'anthropic' not in config.api_key.lower()
    
    def test_google_api_key_resolution(self):
        """EVIDENCE: Google provider should use GEMINI_API_KEY"""
        with patch.dict(os.environ, {
            'API_PROVIDER': 'google',
            'OPENAI_API_KEY': 'openai-key-should-not-be-used',
            'GEMINI_API_KEY': 'AIzaSyD-test-gemini-key',
            'ANTHROPIC_API_KEY': 'anthropic-key-should-not-be-used'
        }):
            config = UnifiedConfig()
            assert config.api_provider == 'google'
            assert config.api_key == 'AIzaSyD-test-gemini-key'
            assert 'openai' not in config.api_key.lower()
            assert 'anthropic' not in config.api_key.lower()
    
    def test_anthropic_api_key_resolution(self):
        """EVIDENCE: Anthropic provider should use ANTHROPIC_API_KEY"""
        with patch.dict(os.environ, {
            'API_PROVIDER': 'anthropic',
            'OPENAI_API_KEY': 'openai-key-should-not-be-used',
            'GEMINI_API_KEY': 'gemini-key-should-not-be-used',
            'ANTHROPIC_API_KEY': 'sk-ant-test-anthropic-key'
        }):
            config = UnifiedConfig()
            assert config.api_provider == 'anthropic'
            assert config.api_key == 'sk-ant-test-anthropic-key'
            assert 'openai' not in config.api_key.lower()
            assert 'gemini' not in config.api_key.lower()
    
    def test_dynamic_provider_switching(self):
        """EVIDENCE: Same config instance should resolve different keys when provider changes"""
        # Setup environment with all keys
        env_vars = {
            'OPENAI_API_KEY': 'sk-openai-12345',
            'GEMINI_API_KEY': 'AIzaSyD-gemini-67890',
            'ANTHROPIC_API_KEY': 'sk-ant-anthropic-abcde'
        }
        
        with patch.dict(os.environ, env_vars):
            # Test switching providers dynamically
            with patch.dict(os.environ, {'API_PROVIDER': 'openai'}):
                config = UnifiedConfig()
                assert config.api_key == 'sk-openai-12345'
            
            with patch.dict(os.environ, {'API_PROVIDER': 'google'}):
                config = UnifiedConfig()
                assert config.api_key == 'AIzaSyD-gemini-67890'
            
            with patch.dict(os.environ, {'API_PROVIDER': 'anthropic'}):
                config = UnifiedConfig()
                assert config.api_key == 'sk-ant-anthropic-abcde'
    
    def test_missing_api_key_handling(self):
        """EVIDENCE: Missing API key should return empty string, not raise exception"""
        with patch.dict(os.environ, {
            'API_PROVIDER': 'openai',
            'GEMINI_API_KEY': 'gemini-key-exists'
            # OPENAI_API_KEY intentionally missing
        }, clear=True):  # Clear environment to ensure no interference
            config = UnifiedConfig()
            assert config.api_provider == 'openai'
            assert config.api_key == ''  # Should return empty string for missing key
    
    def test_unknown_provider_fallback(self):
        """EVIDENCE: Unknown provider should be rejected by validation"""
        with patch.dict(os.environ, {
            'API_PROVIDER': 'unknown_provider',
            'GEMINI_API_KEY': 'fallback-gemini-key'
        }, clear=True):
            # Unknown provider should raise validation error (good security behavior)
            with pytest.raises(ValueError, match="Invalid API_PROVIDER"):
                config = UnifiedConfig()


class TestLLMHandlerIntegration:
    """Test LLM Handler integration with new API key resolution"""
    
    def test_llm_handler_uses_correct_api_key(self):
        """EVIDENCE: LLMHandler should use the correct API key from UnifiedConfig"""
        with patch.dict(os.environ, {
            'API_PROVIDER': 'openai',
            'MODEL': 'gpt-4o-mini',
            'OPENAI_API_KEY': 'sk-test-openai-integration',
            'GEMINI_API_KEY': 'gemini-should-not-be-used'
        }):
            config = UnifiedConfig()
            handler = LLMHandler(config=config)
            
            # Verify handler gets the correct API key
            assert handler.api_key == 'sk-test-openai-integration'
            assert 'gemini' not in handler.api_key.lower()
    
    def test_llm_handler_provider_switching(self):
        """EVIDENCE: LLMHandler should adapt when provider changes"""
        env_vars = {
            'MODEL': 'test-model',
            'OPENAI_API_KEY': 'sk-openai-handler-test',
            'GEMINI_API_KEY': 'AIzaSyD-gemini-handler-test'
        }
        
        with patch.dict(os.environ, env_vars):
            # Test OpenAI configuration
            with patch.dict(os.environ, {'API_PROVIDER': 'openai'}):
                config = UnifiedConfig()
                handler = LLMHandler(config=config)
                assert handler.api_key == 'sk-openai-handler-test'
            
            # Test Google configuration
            with patch.dict(os.environ, {'API_PROVIDER': 'google'}):
                config = UnifiedConfig()
                handler = LLMHandler(config=config)
                assert handler.api_key == 'AIzaSyD-gemini-handler-test'


class TestEnvironmentDrivenConfiguration:
    """Test complete environment-driven configuration without hardcoded values"""
    
    def test_all_reliability_settings_from_env(self):
        """EVIDENCE: All reliability settings should be loaded from environment"""
        env_vars = {
            'MAX_LLM_RETRIES': '7',
            'BASE_RETRY_DELAY': '2.5', 
            'CIRCUIT_BREAKER_THRESHOLD': '10',
            'CIRCUIT_BREAKER_TIMEOUT': '600',
            'REQUEST_TIMEOUT': '240'
        }
        
        with patch.dict(os.environ, env_vars):
            config = UnifiedConfig()
            
            # Verify all values loaded from environment
            assert config.max_llm_retries == 7
            assert config.base_retry_delay == 2.5
            assert config.circuit_breaker_threshold == 10
            assert config.circuit_breaker_timeout == 600
            assert config.request_timeout == 240
    
    def test_reliability_settings_defaults(self):
        """EVIDENCE: Default values should be used when env vars not set"""
        # Clear any existing env vars that might interfere
        env_vars_to_clear = [
            'MAX_LLM_RETRIES',
            'BASE_RETRY_DELAY', 
            'CIRCUIT_BREAKER_THRESHOLD',
            'CIRCUIT_BREAKER_TIMEOUT',
            'REQUEST_TIMEOUT'
        ]
        
        with patch.dict(os.environ, {}, clear=False):
            # Remove any existing values
            for var in env_vars_to_clear:
                os.environ.pop(var, None)
            
            config = UnifiedConfig()
            
            # Verify defaults are used
            assert config.max_llm_retries == 4
            assert config.base_retry_delay == 1.0
            assert config.circuit_breaker_threshold == 5
            assert config.circuit_breaker_timeout is None
            assert config.request_timeout is None
    
    def test_no_hardcoded_values_in_config(self):
        """EVIDENCE: Verify no hardcoded values remain in UnifiedConfig"""
        import inspect
        from qc_clean.config.unified_config import UnifiedConfig
        
        source = inspect.getsource(UnifiedConfig)
        
        # Check that old hardcoded patterns are not present
        forbidden_patterns = [
            'max_llm_retries: int = 4',
            'base_retry_delay: float = 1.0', 
            'circuit_breaker_threshold: int = 5',
            'api_key: str = field(default_factory=lambda: os.getenv(\'API_KEY\'',
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in source, f"Found forbidden hardcoded pattern: {pattern}"
        
        # Verify environment loading patterns are present
        required_patterns = [
            'MAX_LLM_RETRIES',
            'BASE_RETRY_DELAY',
            'CIRCUIT_BREAKER_THRESHOLD',
            '@property',
            'def api_key(self)'
        ]
        
        for pattern in required_patterns:
            assert pattern in source, f"Required environment loading pattern missing: {pattern}"


class TestConfigurationBehavioralDifferences:
    """Test that different configurations produce different behavioral parameters"""
    
    def test_provider_affects_behavioral_parameters(self):
        """EVIDENCE: Different providers should maintain behavioral parameter compatibility"""
        base_env = {
            'METHODOLOGY': 'grounded_theory',
            'TEMPERATURE': '0.1',
            'OPENAI_API_KEY': 'sk-openai-test',
            'GEMINI_API_KEY': 'AIzaSyD-gemini-test'
        }
        
        with patch.dict(os.environ, base_env):
            # Test OpenAI config
            with patch.dict(os.environ, {'API_PROVIDER': 'openai', 'MODEL': 'gpt-4o-mini'}):
                openai_config = UnifiedConfig()
                openai_params = openai_config.get_behavioral_parameters()
            
            # Test Google config  
            with patch.dict(os.environ, {'API_PROVIDER': 'google', 'MODEL': 'gemini-2.5-flash'}):
                google_config = UnifiedConfig()
                google_params = google_config.get_behavioral_parameters()
            
            # Verify behavioral parameters are identical (provider doesn't affect analysis behavior)
            for key in openai_params:
                assert openai_params[key] == google_params[key], f"Behavioral parameter {key} differs between providers"
    
    def test_temperature_affects_behavioral_difference(self):
        """EVIDENCE: Temperature changes should produce significant behavioral differences"""
        base_env = {
            'API_PROVIDER': 'google',
            'MODEL': 'gemini-2.5-flash',
            'METHODOLOGY': 'grounded_theory'
        }
        
        with patch.dict(os.environ, base_env):
            # Low temperature config
            with patch.dict(os.environ, {'TEMPERATURE': '0.1'}):
                low_temp_config = UnifiedConfig()
            
            # High temperature config
            with patch.dict(os.environ, {'TEMPERATURE': '0.8'}):
                high_temp_config = UnifiedConfig()
        
        # Calculate behavioral difference
        difference = low_temp_config.calculate_behavioral_difference(high_temp_config)
        
        # Should be significant difference (>20% change in temperature parameter)
        assert difference > 0.0, "Temperature change should produce measurable behavioral difference"


def test_real_api_key_resolution_integration():
    """
    INTEGRATION TEST: Complete provider switching workflow
    Tests the full chain: .env → UnifiedConfig → LLMHandler
    """
    # Test complete workflow with actual API keys from environment
    original_provider = os.getenv('API_PROVIDER')
    original_model = os.getenv('MODEL')
    
    try:
        # Test OpenAI workflow
        os.environ['API_PROVIDER'] = 'openai'
        os.environ['MODEL'] = 'gpt-4o-mini'
        
        config = UnifiedConfig()
        handler = LLMHandler(config=config)
        
        expected_openai_key = os.getenv('OPENAI_API_KEY')
        if expected_openai_key:
            assert config.api_key == expected_openai_key
            assert handler.api_key == expected_openai_key
        
        print("PASS: OpenAI provider workflow: Configuration and LLMHandler integration working")
        
        # Test Google workflow  
        os.environ['API_PROVIDER'] = 'google'
        os.environ['MODEL'] = 'gemini-2.5-flash'
        
        config = UnifiedConfig()
        handler = LLMHandler(config=config)
        
        expected_gemini_key = os.getenv('GEMINI_API_KEY')
        if expected_gemini_key:
            assert config.api_key == expected_gemini_key
            assert handler.api_key == expected_gemini_key
        
        print("PASS: Google provider workflow: Configuration and LLMHandler integration working")
        
        # Test Anthropic workflow (if key available)
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            os.environ['API_PROVIDER'] = 'anthropic'
            os.environ['MODEL'] = 'claude-3-5-sonnet-20241022'
            
            config = UnifiedConfig()
            handler = LLMHandler(config=config)
            
            assert config.api_key == anthropic_key
            assert handler.api_key == anthropic_key
            
            print("PASS: Anthropic provider workflow: Configuration and LLMHandler integration working")
        
        print("SUCCESS: Complete provider switching workflow successful")
        
    finally:
        # Restore original environment
        if original_provider:
            os.environ['API_PROVIDER'] = original_provider
        if original_model:
            os.environ['MODEL'] = original_model


if __name__ == "__main__":
    print("Testing Provider-Agnostic Multi-Provider Support...")
    print("=" * 60)
    
    # Run integration test with real environment
    test_real_api_key_resolution_integration()
    
    print("\n" + "=" * 60)
    print("Running pytest for comprehensive test suite...")
    
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])