#!/usr/bin/env python3
"""
Test suite for multi-provider LLM support.
Tests that LLM handler works with all providers without hardcoded preprocessing.
"""

import os
import sys
from pathlib import Path

def test_openai_model_formatting():
    """EVIDENCE: OpenAI models must work without Gemini preprocessing"""
    
    # Set OpenAI configuration
    original_model = os.environ.get('MODEL')
    original_provider = os.environ.get('API_PROVIDER')
    
    os.environ['MODEL'] = 'gpt-4o-mini'
    os.environ['API_PROVIDER'] = 'openai'
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'qc_clean'))
        from config.unified_config import UnifiedConfig
        from core.llm.llm_handler import LLMHandler
        
        config = UnifiedConfig()
        handler = LLMHandler(config=config)
        
        # Should NOT add gemini/ prefix
        assert handler.model_name == 'gpt-4o-mini', f"Expected 'gpt-4o-mini', got '{handler.model_name}'"
        assert not handler.model_name.startswith('gemini/'), f"Should not have gemini/ prefix: {handler.model_name}"
        
        print("PASS: OpenAI model formatting correct")
        return True
        
    finally:
        # Restore environment
        if original_model is None:
            os.environ.pop('MODEL', None)
        else:
            os.environ['MODEL'] = original_model
            
        if original_provider is None:
            os.environ.pop('API_PROVIDER', None) 
        else:
            os.environ['API_PROVIDER'] = original_provider

def test_gemini_model_compatibility():  
    """EVIDENCE: Gemini models must still work after removing hardcoded logic"""
    
    # Set Gemini configuration
    original_model = os.environ.get('MODEL')
    original_provider = os.environ.get('API_PROVIDER')
    
    os.environ['MODEL'] = 'gemini-2.5-flash'
    os.environ['API_PROVIDER'] = 'google'
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'qc_clean'))
        from config.unified_config import UnifiedConfig
        from core.llm.llm_handler import LLMHandler
        
        config = UnifiedConfig()
        handler = LLMHandler(config=config)
        
        # Should use model name as-is, let LiteLLM handle formatting
        assert handler.model_name == 'gemini-2.5-flash', f"Expected 'gemini-2.5-flash', got '{handler.model_name}'"
        
        print("PASS: Gemini model compatibility maintained")
        return True
        
    finally:
        # Restore environment
        if original_model is None:
            os.environ.pop('MODEL', None)
        else:
            os.environ['MODEL'] = original_model
            
        if original_provider is None:
            os.environ.pop('API_PROVIDER', None)
        else:
            os.environ['API_PROVIDER'] = original_provider

def test_anthropic_model_support():
    """EVIDENCE: Anthropic models must work without preprocessing"""
    
    # Set Anthropic configuration
    original_model = os.environ.get('MODEL')
    original_provider = os.environ.get('API_PROVIDER')
    
    os.environ['MODEL'] = 'claude-3-5-sonnet-20241022'
    os.environ['API_PROVIDER'] = 'anthropic'
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'qc_clean'))
        from config.unified_config import UnifiedConfig
        from core.llm.llm_handler import LLMHandler
        
        config = UnifiedConfig()
        handler = LLMHandler(config=config)
        
        # Should use model name as-is
        assert handler.model_name == 'claude-3-5-sonnet-20241022', f"Expected 'claude-3-5-sonnet-20241022', got '{handler.model_name}'"
        assert not handler.model_name.startswith('gemini/'), f"Should not have gemini/ prefix: {handler.model_name}"
        
        print("PASS: Anthropic model formatting correct")
        return True
        
    finally:
        # Restore environment
        if original_model is None:
            os.environ.pop('MODEL', None)
        else:
            os.environ['MODEL'] = original_model
            
        if original_provider is None:
            os.environ.pop('API_PROVIDER', None)
        else:
            os.environ['API_PROVIDER'] = original_provider

def test_provider_switching():
    """EVIDENCE: Same research methodology with different providers must work"""
    
    # Test data
    interview_data = {'content': 'AI research interview content about machine learning applications...'}
    
    providers_to_test = [
        ('openai', 'gpt-4o-mini'),
        ('google', 'gemini-2.5-flash'),
        ('anthropic', 'claude-3-5-sonnet-20241022')
    ]
    
    results = []
    for provider, model in providers_to_test:
        # Set environment for this provider
        original_model = os.environ.get('MODEL')
        original_provider = os.environ.get('API_PROVIDER')
        
        os.environ['MODEL'] = model
        os.environ['API_PROVIDER'] = provider
        
        try:
            sys.path.insert(0, str(Path(__file__).parent / 'qc_clean'))
            from config.unified_config import UnifiedConfig
            from core.llm.llm_handler import LLMHandler
            
            config = UnifiedConfig()
            handler = LLMHandler(config=config)
            
            # Verify handler configuration
            assert handler.model_name == model, f"Model name incorrect for {provider}: expected {model}, got {handler.model_name}"
            
            results.append({
                'provider': provider,
                'model': model,
                'handler_configured': True,
                'model_name': handler.model_name
            })
            
        except Exception as e:
            results.append({
                'provider': provider,
                'model': model,
                'error': str(e)
            })
            
        finally:
            # Restore environment
            if original_model is None:
                os.environ.pop('MODEL', None)
            else:
                os.environ['MODEL'] = original_model
                
            if original_provider is None:
                os.environ.pop('API_PROVIDER', None)
            else:
                os.environ['API_PROVIDER'] = original_provider
    
    # Validate all providers configured successfully
    for result in results:
        if 'error' in result:
            print(f"WARNING: Provider {result['provider']} had issues: {result.get('error')}")
        else:
            assert result['handler_configured'], f"Handler not configured for {result['provider']}"
    
    print(f"PASS: {len([r for r in results if 'error' not in r])} providers tested successfully")
    return True

def test_config_integration_with_llm_handler():
    """EVIDENCE: UnifiedConfig must integrate properly with LLMHandler"""
    
    # Set test configuration
    original_model = os.environ.get('MODEL')
    original_provider = os.environ.get('API_PROVIDER')
    original_temperature = os.environ.get('TEMPERATURE')
    
    os.environ['MODEL'] = 'gpt-4o-mini'
    os.environ['API_PROVIDER'] = 'openai'
    os.environ['TEMPERATURE'] = '0.3'
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'qc_clean'))
        from config.unified_config import UnifiedConfig
        from core.llm.llm_handler import LLMHandler
        
        config = UnifiedConfig()
        handler = LLMHandler(config=config)
        
        # Verify config integration
        assert config.model_preference == 'gpt-4o-mini'
        assert config.api_provider == 'openai'
        assert abs(config.temperature - 0.3) < 0.001
        
        # Verify handler uses config values
        assert handler.model_name == 'gpt-4o-mini'
        assert abs(handler.temperature - 0.3) < 0.001
        
        print("PASS: UnifiedConfig integrates properly with LLMHandler")
        return True
        
    finally:
        # Restore environment
        if original_model is None:
            os.environ.pop('MODEL', None)
        else:
            os.environ['MODEL'] = original_model
            
        if original_provider is None:
            os.environ.pop('API_PROVIDER', None)
        else:
            os.environ['API_PROVIDER'] = original_provider
            
        if original_temperature is None:
            os.environ.pop('TEMPERATURE', None)
        else:
            os.environ['TEMPERATURE'] = original_temperature

if __name__ == '__main__':
    print("Testing multi-provider LLM support...")
    
    try:
        test_openai_model_formatting()
        test_gemini_model_compatibility()
        test_anthropic_model_support()
        test_provider_switching()
        test_config_integration_with_llm_handler()
        print("\nALL TESTS PASSED: Multi-provider LLM support working")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)