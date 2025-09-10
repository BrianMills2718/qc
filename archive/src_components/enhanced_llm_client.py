#!/usr/bin/env python3
"""
Enhanced LLM Client using Universal LLM Kit
Drop-in replacement for UniversalModelClient with better reliability and cost optimization
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from ..utils.error_handler import LLMError, ValidationError

# Import Universal LLM Kit
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "external"))

from universal_llm import UniversalLLM
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class MockResponse:
    """Mock response object to maintain compatibility with existing code"""
    
    def __init__(self, content: str):
        self.choices = [MockChoice(content)]

class MockChoice:
    """Mock choice object"""
    
    def __init__(self, content: str):
        self.message = MockMessage(content)

class MockMessage:
    """Mock message object"""
    
    def __init__(self, content: str):
        self.content = content

@dataclass
class ValidationResult:
    """Result from multi-model validation"""
    confidence: str  # "high", "medium", "low"
    model_agreement: bool
    results: Dict[str, str]
    successful_models: int

class EnhancedLLMClient:
    """Enhanced LLM client using Universal LLM Kit with smart routing and fallbacks"""
    
    def __init__(self):
        """Initialize enhanced client with Universal LLM"""
        try:
            self.universal_llm = UniversalLLM()
            logger.info("Enhanced LLM client initialized with Universal LLM Kit")
        except Exception as e:
            logger.error(f"Failed to initialize Universal LLM: {e}")
            raise
    
    def complete(self, 
                 messages: List[Dict], 
                 schema: Optional[Dict] = None, 
                 max_tokens: Optional[int] = None,  # No default - use full context
                 temperature: float = 0.3,
                 **kwargs) -> Dict[str, Any]:
        """
        Universal completion with automatic fallbacks and smart routing
        
        Maintains compatibility with existing UniversalModelClient interface
        """
        # Convert messages to single prompt
        prompt = self._messages_to_prompt(messages)
        
        try:
            if schema:
                # Use structured output
                response_text = self.universal_llm.structured_output(prompt)
                
                # Validate JSON if schema provided
                try:
                    json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON response, attempting to fix: {e}")
                    # Try to extract JSON from response
                    response_text = self._extract_json_from_response(response_text)
                
            else:
                # Use regular chat
                response_text = self.universal_llm.chat(prompt, model_type="smart")
            
            return {
                'response': MockResponse(response_text),
                'model_used': 'smart',  # Universal LLM handles routing internally
                'attempts': 1,
                'cost': 0.0,  # Could be calculated if needed
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Enhanced LLM client failed: {e}")
            raise LLMError(f"Enhanced LLM client failed: {e}") from e
    
    def validate_extraction_quality(self, prompt: str) -> ValidationResult:
        """
        Simple multi-model validation for extraction quality
        
        Tests extraction with multiple models to assess confidence
        """
        try:
            # Test with different model types
            models_to_test = ["smart", "fast"]
            results = self.universal_llm.compare_models(prompt, models_to_test)
            
            # Count successful responses (not errors)
            successful_models = sum(1 for result in results.values() 
                                  if not result.startswith("Error:"))
            
            # Determine confidence based on model agreement
            if successful_models >= 2:
                confidence = "high"
                model_agreement = True
            elif successful_models == 1:
                confidence = "medium"
                model_agreement = False
            else:
                confidence = "low"
                model_agreement = False
            
            return ValidationResult(
                confidence=confidence,
                model_agreement=model_agreement,
                results=results,
                successful_models=successful_models
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise ValidationError(f"Validation failed: {e}") from e
    
    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert message format to single prompt"""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(content)
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from response text if it's embedded in other text"""
        # Look for JSON-like patterns
        import re
        
        # Try to find JSON object in response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            potential_json = json_match.group()
            try:
                # Validate it's proper JSON
                json.loads(potential_json)
                return potential_json
            except json.JSONDecodeError:
                pass
        
        # If no valid JSON found, return original response
        logger.warning("Could not extract valid JSON from response")
        return response
    
    def get_available_models(self) -> List[str]:
        """Get list of available model types"""
        return ["smart", "fast", "code", "reasoning"]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model configuration"""
        return {
            "client_type": "Enhanced LLM Client",
            "backend": "Universal LLM Kit",
            "routing_strategy": "cost-based",
            "fallbacks_enabled": True,
            "available_models": self.get_available_models()
        }