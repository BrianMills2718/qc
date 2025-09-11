#!/usr/bin/env python3
"""
Universal Model Client with Automatic Fallbacks and Structured Output
Supports all major LLM providers with intelligent fallback handling
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion
import litellm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TriggerCondition(Enum):
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit" 
    ERROR = "error"
    TOKEN_LIMIT = "token_limit"

@dataclass
class ModelConfig:
    name: str
    litellm_name: str
    supports_structured_output: bool
    max_tokens: int
    
class UniversalModelClient:
    def __init__(self, env_path: Optional[str] = None):
        """Initialize the universal model client"""
        if env_path:
            load_dotenv(env_path)
        else:
            # Load from project root
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / '.env'
            
            if env_file.exists():
                logger.info(f"Loading .env from: {env_file}")
                load_dotenv(env_file)
            else:
                logger.info("Loading .env from default location")
                load_dotenv()
        
        self.api_keys = self._load_api_keys()
        self.models = self._load_model_configs()
        self.fallback_config = self._load_fallback_config()
        
        # Debug: print loaded models
        logger.info(f"Loaded {len(self.models)} models: {list(self.models.keys())}")
        
        # Set up litellm with API keys
        self._configure_litellm()
        
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment"""
        return {
            'openai': os.getenv('OPENAI_API_KEY'),
            'gemini': os.getenv('GEMINI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY')
        }
    
    def _load_model_configs(self) -> Dict[str, ModelConfig]:
        """Load model configurations from environment"""
        models = {}
        
        # Define all supported models
        model_vars = [
            'GEMINI_2_5_PRO', 'GEMINI_2_5_FLASH', 'GEMINI_2_5_FLASH_LITE',
            'GPT_4_1', 'O4_MINI', 'O3',
            'CLAUDE_OPUS_4', 'CLAUDE_SONNET_4', 'CLAUDE_SONNET_3_7', 'CLAUDE_HAIKU_3_5'
        ]
        
        for var in model_vars:
            config_str = os.getenv(var)
            logger.debug(f"Loading {var}: {config_str}")
            if config_str:
                parts = config_str.split(',')
                if len(parts) >= 3:
                    model_key = var.lower()  
                    models[model_key] = ModelConfig(
                        name=model_key,
                        litellm_name=parts[0],
                        supports_structured_output=parts[1].lower() == 'true',
                        max_tokens=int(parts[2])
                    )
                    logger.debug(f"Added model {model_key}: {models[model_key]}")
        
        logger.debug(f"Total models loaded: {len(models)}")
        return models
    
    def _load_fallback_config(self) -> Dict[str, Any]:
        """Load fallback configuration"""
        return {
            'primary_model': os.getenv('PRIMARY_MODEL', 'gemini_2_5_flash'),
            # FALLBACK MODELS REMOVED - FAIL-FAST ENFORCEMENT
            'timeout_seconds': None,  # REMOVED: No timeout limits
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'fallback_on_rate_limit': False,  # FAIL-FAST: No fallback on rate limits
            'fallback_on_timeout': False,    # FAIL-FAST: No fallback on timeouts  
            'fallback_on_error': False,      # FAIL-FAST: No fallback on errors
            'schema_var_name': os.getenv('SCHEMA_VAR_NAME', 'OUTPUT_SCHEMA')
        }
    
    def _configure_litellm(self):
        """Configure litellm with API keys"""
        if self.api_keys['openai']:
            os.environ['OPENAI_API_KEY'] = self.api_keys['openai']
        if self.api_keys['gemini']:
            os.environ['GEMINI_API_KEY'] = self.api_keys['gemini']
        if self.api_keys['anthropic']:
            os.environ['ANTHROPIC_API_KEY'] = self.api_keys['anthropic']
    
    def _get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get model configuration by name"""
        # Try exact match first
        if model_name in self.models:
            return self.models[model_name]
        
        # Try to find by litellm name
        for config in self.models.values():
            if config.litellm_name == model_name:
                return config
        
        # Debug: print available models if not found
        logger.debug(f"Available models: {list(self.models.keys())}")
        logger.debug(f"Looking for: {model_name}")
        
        return None
    
    def _should_fallback(self, error: Exception, trigger_conditions: List[TriggerCondition]) -> bool:
        """Determine if we should fallback based on error and conditions"""
        error_str = str(error).lower()
        
        if TriggerCondition.RATE_LIMIT in trigger_conditions:
            if 'rate limit' in error_str or 'rate_limit' in error_str or '429' in error_str:
                return True
        
        if TriggerCondition.TIMEOUT in trigger_conditions:
            if 'timeout' in error_str or 'timed out' in error_str:
                return True
        
        if TriggerCondition.TOKEN_LIMIT in trigger_conditions:
            if 'token limit' in error_str or 'max_tokens' in error_str or 'context length' in error_str:
                return True
        
        if TriggerCondition.ERROR in trigger_conditions:
            return True  # Fallback on any error
        
        return False
    
    def _prepare_structured_output(self, model_config: ModelConfig, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Prepare structured output parameters based on model capabilities"""
        if not schema:
            return {}
        
        if model_config.supports_structured_output:
            # Use native structured output
            return {
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_output",
                        "schema": schema,
                        "strict": True
                    }
                }
            }
        else:
            # Use JSON mode only (for models like o4-mini)
            return {
                "response_format": {"type": "json_object"}
            }
    
    def _inject_schema_in_prompt(self, messages: List[Dict], schema: Optional[Dict] = None) -> List[Dict]:
        """Inject schema into prompt for models without native structured output"""
        if not schema:
            return messages
        
        # Add schema to the last user message
        modified_messages = messages.copy()
        schema_instruction = f"\n\nPlease format your response as JSON matching this exact schema: {json.dumps(schema)}"
        
        # Find the last user message and append schema
        for i in range(len(modified_messages) - 1, -1, -1):
            if modified_messages[i].get('role') == 'user':
                modified_messages[i]['content'] += schema_instruction
                break
        
        return modified_messages
    
    def complete(self, 
                 messages: List[Dict],
                 model: Optional[str] = None,
                 schema: Optional[Dict] = None,
                 fallback_models: Optional[List[str]] = None,
                 trigger_conditions: Optional[List[TriggerCondition]] = None,
                 **kwargs) -> Dict[str, Any]:
        """
        Universal completion with automatic fallbacks
        
        Args:
            messages: List of message dictionaries
            model: Primary model to use (defaults to env PRIMARY_MODEL)
            schema: JSON schema for structured output
            fallback_models: List of fallback models (defaults to env config)
            trigger_conditions: Conditions that trigger fallback
            **kwargs: Additional parameters for litellm
        
        Returns:
            Dict with response, model_used, attempts, and metadata
        """
        
        # Set defaults
        primary_model = model or self.fallback_config['primary_model']
        fallbacks = fallback_models or self.fallback_config['fallback_models']
        conditions = trigger_conditions or [
            TriggerCondition.RATE_LIMIT if self.fallback_config['fallback_on_rate_limit'] else None,
            TriggerCondition.TIMEOUT if self.fallback_config['fallback_on_timeout'] else None, 
            TriggerCondition.ERROR if self.fallback_config['fallback_on_error'] else None
        ]
        conditions = [c for c in conditions if c is not None]
        
        # Build model sequence
        models_to_try = [primary_model] + fallbacks
        
        attempts = []
        
        for attempt_num, model_name in enumerate(models_to_try):
            model_config = self._get_model_config(model_name)
            if not model_config:
                logger.warning(f"Model config not found for {model_name}, skipping")
                continue
            
            try:
                logger.info(f"Attempt {attempt_num + 1}: Trying {model_config.litellm_name}")
                
                # Prepare parameters
                params = {
                    "model": model_config.litellm_name,
                    "messages": messages,
                    **kwargs
                }
                
                # Handle structured output
                if schema:
                    if model_config.supports_structured_output:
                        # Use native structured output
                        params.update(self._prepare_structured_output(model_config, schema))
                    else:
                        # Inject schema in prompt
                        params["messages"] = self._inject_schema_in_prompt(messages, schema)
                        params["response_format"] = {"type": "json_object"}
                
                # REMOVED: Set timeout - no timeout limits
                # params["timeout"] = self.fallback_config['timeout_seconds']
                
                # Make the call
                start_time = time.time()
                response = completion(**params)
                end_time = time.time()
                
                # Record successful attempt
                attempts.append({
                    "model": model_config.litellm_name,
                    "attempt": attempt_num + 1,
                    "success": True,
                    "duration": end_time - start_time,
                    "error": None
                })
                
                return {
                    "response": response,
                    "model_used": model_config.litellm_name,
                    "attempts": attempts,
                    "total_attempts": len(attempts),
                    "schema_used": schema is not None,
                    "structured_output_native": model_config.supports_structured_output if schema else None
                }
                
            except Exception as e:
                end_time = time.time()
                
                # Record failed attempt
                attempts.append({
                    "model": model_config.litellm_name,
                    "attempt": attempt_num + 1,
                    "success": False,
                    "duration": end_time - start_time,
                    "error": str(e)
                })
                
                logger.warning(f"Attempt {attempt_num + 1} failed with {model_config.litellm_name}: {e}")
                
                # Check if we should fallback
                if attempt_num < len(models_to_try) - 1:  # Not the last model
                    if self._should_fallback(e, conditions):
                        logger.info(f"Falling back to next model due to: {e}")
                        continue
                    else:
                        logger.info(f"Not falling back, error doesn't match trigger conditions")
                        break
                else:
                    logger.error("All models exhausted")
        
        # All models failed
        raise Exception(f"All models failed. Attempts: {attempts}")

def main():
    """Example usage"""
    client = UniversalModelClient()
    
    # Example schema
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "key_points": {
                "type": "array",
                "items": {"type": "string"}
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "required": ["summary", "key_points", "confidence"],
        "additionalProperties": False
    }
    
    # Test with structured output
    result = client.complete(
        messages=[
            {"role": "user", "content": "Analyze the benefits of renewable energy"}
        ],
        schema=schema
    )
    
    print(f"Model used: {result['model_used']}")
    print(f"Total attempts: {result['total_attempts']}")
    print(f"Response: {result['response'].choices[0].message.content}")

if __name__ == "__main__":
    main()