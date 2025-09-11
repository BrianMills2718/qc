"""
LLM Handler for Code-First Extraction
Uses LiteLLM with real structured output for gemini-2.5-flash
"""

import json
import logging
import os
import asyncio
import random
import time
from typing import Dict, List, Optional, Any, Type
from pydantic import BaseModel
import litellm
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.utils.error_handler import LLMError
from config.methodology_config import GroundedTheoryConfig

# Support for new UnifiedConfig - try import, fall back to old config for compatibility
try:
    from config.unified_config import UnifiedConfig
    ConfigType = UnifiedConfig
except ImportError:
    ConfigType = GroundedTheoryConfig

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure LiteLLM
litellm.set_verbose = False  # Set to True for debugging


class LLMHandler:
    """
    Handler for LLM operations with structured extraction support.
    Does NOT set max_tokens by default - uses full context window.
    """
    
    def __init__(self, 
                 model_name: str = "gpt-4o-mini", 
                 temperature: float = 0.1,
                 config = None,  # Can be UnifiedConfig or GroundedTheoryConfig
                 max_retries: int = 4,
                 base_delay: float = 1.0):
        """
        Initialize LLM handler with LiteLLM and retry logic
        
        Args:
            model_name: Model to use (default: gpt-4o-mini)
            temperature: Temperature for generation (default: 0.1 for consistency)
            config: Configuration object for LLM parameters (UnifiedConfig or GroundedTheoryConfig)
            max_retries: Maximum number of retry attempts (default: 4)
            base_delay: Base delay for exponential backoff (default: 1.0 seconds)
        """
        
        # Apply configuration if provided
        if config:
            self.model_name = config.model_preference
            self.temperature = config.temperature
            self.default_max_tokens = getattr(config, 'max_tokens', None)
            
            # Get API key based on config type
            if hasattr(config, 'api_key') and config.api_key:
                # New UnifiedConfig has api_key field
                self.api_key = config.api_key
            else:
                # Fall back to environment-specific key based on provider
                api_provider = getattr(config, 'api_provider', 'google')
                if api_provider == 'openai':
                    self.api_key = os.getenv("OPENAI_API_KEY")
                elif api_provider == 'anthropic':
                    self.api_key = os.getenv("ANTHROPIC_API_KEY")
                else:  # google/gemini default
                    self.api_key = os.getenv("GEMINI_API_KEY")
            
            # Check if config has retry settings
            if hasattr(config, 'max_llm_retries'):
                self.max_retries = config.max_llm_retries
                self.base_delay = getattr(config, 'base_retry_delay', base_delay)
            else:
                self.max_retries = max_retries
                self.base_delay = base_delay
            
            logger.info(f"LLM Handler initialized from config: {config.model_preference}, temp={config.temperature}, retries={self.max_retries}")
        else:
            # Use model name as-is - let LiteLLM handle provider-specific formatting
            self.model_name = model_name
            self.temperature = temperature
            self.default_max_tokens = None
            self.max_retries = max_retries
            self.base_delay = base_delay
            
            # Default to Gemini API key for backward compatibility
            self.api_key = os.getenv("GEMINI_API_KEY")
            
            logger.info(f"LLM Handler initialized with defaults: {self.model_name}, temp={temperature}, retries={max_retries}")
        
        # Validate API key is available
        if not self.api_key:
            provider = getattr(config, 'api_provider', 'google') if config else 'google'
            raise ValueError(f"No API key found for provider '{provider}'. Please set the appropriate API key in environment variables.")
        
        # Store config for access to other parameters
        self.config = config
        
        # Initialize retry and circuit breaker state
        self.logger = logging.getLogger(__name__)
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_breaker_threshold = getattr(config, 'circuit_breaker_threshold', 5) if config else 5
        self.circuit_breaker_timeout = None  # No timeout limits
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        delay = self.base_delay * (2 ** attempt)
        # Add jitter: 50% to 150% of calculated delay
        jitter = random.uniform(0.5, 1.5)
        return min(delay * jitter, 30.0)  # Cap at 30 seconds
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if error is worth retrying"""
        error_str = str(error).lower()
        retryable_patterns = [
            "http 500",
            "internal server error", 
            "service unavailable",
            "timeout",
            "connection reset",
            "temporary failure",
            "rate limit",
            "overloaded",
            "empty content",  # Server overload can cause empty responses
            "no content",
            "connection error",
            "network error",
            "no json found",  # Server overload can cause malformed JSON responses
            "json parse error",
            "invalid json",
            "unterminated string",
            "malformed json",
            "expecting",  # JSON syntax errors like "Expecting ',' delimiter"
            "delimiter"
        ]
        return any(pattern in error_str for pattern in retryable_patterns)
    
    def _should_circuit_break(self) -> bool:
        """Check if circuit breaker should be triggered"""
        if self.failure_count < self.circuit_breaker_threshold:
            return False
            
        if self.last_failure_time is None:
            return False
            
        time_since_failure = time.time() - self.last_failure_time
        # No timeout limits - circuit breaker disabled
        return False
    
    def _record_success(self):
        """Record successful API call"""
        self.failure_count = 0
        self.last_failure_time = None
    
    def _record_failure(self):
        """Record failed API call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
    
    async def _retry_with_backoff(self, operation, operation_name: str, *args, **kwargs):
        """Generic retry wrapper with exponential backoff"""
        
        if self._should_circuit_break():
            raise Exception(f"Circuit breaker open for {operation_name}. Too many recent failures.")
        
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"{operation_name} attempt {attempt + 1}/{self.max_retries + 1}")
                
                result = await operation(*args, **kwargs)
                self._record_success()
                
                if attempt > 0:
                    self.logger.info(f"{operation_name} succeeded after {attempt} retries")
                    
                return result
                
            except Exception as e:
                last_error = e
                self._record_failure()
                
                self.logger.warning(f"{operation_name} attempt {attempt + 1} failed: {e}")
                
                # Don't retry on non-retryable errors
                if not self._is_retryable_error(e):
                    self.logger.error(f"{operation_name} failed with non-retryable error: {e}")
                    raise e
                
                # Don't delay after last attempt
                if attempt < self.max_retries:
                    delay = self._calculate_backoff_delay(attempt)
                    self.logger.info(f"Retrying {operation_name} in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        error_msg = f"{operation_name} failed after {self.max_retries + 1} attempts. Last error: {last_error}"
        self.logger.error(error_msg)
        raise Exception(error_msg) from last_error
    
    async def extract_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        instructions: Optional[str] = None,
        max_tokens: Optional[int] = None  # None by default - use full context
    ) -> BaseModel:
        """
        Extract structured data from text using LLM with retry logic
        
        Args:
            prompt: The prompt/text to process
            schema: Pydantic model class for the expected output structure
            instructions: Additional instructions for extraction
            max_tokens: Maximum tokens (None = use maximum available)
        
        Returns:
            Instance of the schema model with extracted data
        """
        
        async def _extract_operation():
            # Build the full prompt
            full_prompt = self._build_extraction_prompt(prompt, schema, instructions)
            
            # Prepare messages for LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at extracting structured information from text. "
                              "Return your response as valid JSON that matches the provided schema."
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
            
            # Build kwargs for LiteLLM with JSON mode
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "response_format": {"type": "json_object"},  # Use JSON mode for Gemini
                # Remove timeout limit
            }
            
            # Only add max_tokens if explicitly provided or configured
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
                logger.info(f"Using explicit max_tokens: {max_tokens}")
            elif self.default_max_tokens is not None:
                kwargs["max_tokens"] = self.default_max_tokens
                logger.info(f"Using configured max_tokens: {self.default_max_tokens}")
            else:
                logger.info("Using maximum available context window (no max_tokens limit)")
            
            # Call LiteLLM with JSON mode (async)
            response = await litellm.acompletion(**kwargs)
            
            if not response or not response.choices:
                raise Exception("Empty structured response from LLM API")
            
            response_content = response.choices[0].message.content
            if not response_content:
                raise Exception("Empty content in structured LLM response")
            
            # Parse JSON response
            if isinstance(response_content, dict):
                response_data = response_content
            elif isinstance(response_content, str):
                try:
                    response_data = json.loads(response_content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON directly ({e}), attempting extraction with fixing")
                    response_data = self._extract_and_fix_json_from_text(response_content)
            elif response_content is None:
                # Handle None response by retrying without JSON mode
                logger.warning("Received None response with JSON mode, retrying with text mode")
                return await self._retry_without_json_mode(prompt, schema, instructions, max_tokens)
            else:
                raise ValueError(f"Unexpected response content type: {type(response_content)}")
            
            # Create and validate model instance
            model_instance = schema(**response_data)
            logger.info(f"Successfully extracted {schema.__name__}")
            return model_instance
        
        try:
            return await self._retry_with_backoff(
                _extract_operation,
                f"extract_structured[{schema.__name__}]"
            )
        except Exception as e:
            logger.error(f"Structured extraction failed: {e}")
            raise LLMError(f"Failed to extract {schema.__name__}: {e}") from e
    
    def _build_extraction_prompt(
        self,
        prompt: str,
        schema: Type[BaseModel],
        instructions: Optional[str] = None
    ) -> str:
        """Build the extraction prompt with schema information"""
        
        # Get schema fields and descriptions
        schema_info = self._format_schema_for_prompt(schema)
        
        prompt_parts = [
            f"Extract the following structured information:\n",
            f"\nSCHEMA:\n{schema_info}\n"
        ]
        
        if instructions:
            prompt_parts.append(f"\nADDITIONAL INSTRUCTIONS:\n{instructions}\n")
        
        prompt_parts.append(f"\nTEXT TO ANALYZE:\n{prompt}\n")
        prompt_parts.append(
            f"\nReturn a JSON object that matches the schema exactly. "
            f"Include all required fields and use the correct data types."
        )
        
        return "\n".join(prompt_parts)
    
    def _format_schema_for_prompt(self, schema: Type[BaseModel]) -> str:
        """Format Pydantic schema for inclusion in prompt with full nested structure"""
        lines = [f"Output Type: {schema.__name__}"]
        lines.append("Required Fields:")
        
        # Get full schema with definitions
        schema_dict = schema.model_json_schema()
        properties = schema_dict.get("properties", {})
        required_fields = schema_dict.get("required", [])
        definitions = schema_dict.get("$defs", {})
        
        for field_name, field_info in properties.items():
            field_type = field_info.get("type", "any")
            description = field_info.get("description", "")
            is_required = field_name in required_fields
            
            # Handle array types with nested objects
            if field_info.get("type") == "array" and "items" in field_info:
                items_info = field_info["items"]
                if "$ref" in items_info:
                    # Extract the reference name and get nested structure
                    ref_name = items_info["$ref"].split("/")[-1]
                    if ref_name in definitions:
                        nested_def = definitions[ref_name]
                        field_type = f"array of {ref_name} objects"
                        # Add nested structure details
                        lines.append(f"  - {field_name} ({field_type}) [{('REQUIRED' if is_required else 'OPTIONAL')}]: {description}")
                        lines.append(f"    Each {ref_name} object contains:")
                        nested_props = nested_def.get("properties", {})
                        nested_required = nested_def.get("required", [])
                        for nested_field, nested_info in nested_props.items():
                            nested_type = nested_info.get("type", "any")
                            nested_desc = nested_info.get("description", "")
                            nested_req = "REQUIRED" if nested_field in nested_required else "OPTIONAL"
                            lines.append(f"      - {nested_field} ({nested_type}) [{nested_req}]: {nested_desc}")
                        continue
                    else:
                        field_type = f"array of {ref_name}"
                else:
                    field_type = f"array of {items_info.get('type', 'items')}"
            elif "$ref" in field_info:
                # Reference to another model
                ref_name = field_info["$ref"].split("/")[-1]
                field_type = f"object ({ref_name})"
            
            requirement = "REQUIRED" if is_required else "OPTIONAL"
            lines.append(f"  - {field_name} ({field_type}) [{requirement}]: {description}")
        
        return "\n".join(lines)
    
    def _get_schema_dict(self, schema: Type[BaseModel]) -> Dict[str, Any]:
        """Get schema as dictionary for validation"""
        return schema.model_json_schema()
    
    def _extract_and_fix_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from text with aggressive fixing and partial parsing
        """
        # First try the original method
        try:
            return self._extract_json_from_text(text)
        except (json.JSONDecodeError, ValueError) as original_error:
            logger.info(f"Standard JSON extraction failed ({original_error}), trying aggressive fixes")
            
            # Try more aggressive JSON extraction and fixing
            import re
            
            # Find JSON patterns with more flexibility
            patterns = [
                r'```(?:json)?\s*(\{.*?\})\s*```',  # Code blocks
                r'(\{[^{}]*"open_codes"[^{}]*\[.*?\][^{}]*\})',  # Look for open_codes specifically
                r'(\{.*\})',  # Any object
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.DOTALL)
                for match in matches:
                    # Try to fix and parse each match
                    for attempt in range(3):  # Multiple fixing attempts
                        try:
                            if attempt == 0:
                                # First attempt: basic fixing
                                fixed_json = self._fix_json_string(match)
                            elif attempt == 1:
                                # Second attempt: more aggressive fixing
                                fixed_json = self._aggressive_json_fix(match)
                            else:
                                # Third attempt: partial extraction
                                fixed_json = self._extract_partial_json(match)
                            
                            parsed = json.loads(fixed_json)
                            if isinstance(parsed, dict):
                                logger.info(f"Successfully parsed JSON on attempt {attempt + 1}")
                                return parsed
                                
                        except json.JSONDecodeError as e:
                            logger.debug(f"Attempt {attempt + 1} failed: {e}")
                            continue
            
            # If all attempts failed, raise the original error
            raise original_error

    def _aggressive_json_fix(self, json_str: str) -> str:
        """
        More aggressive JSON fixing for malformed LLM output
        """
        import re
        
        # Start with basic fixing
        json_str = self._fix_json_string(json_str)
        
        # Fix unquoted keys (common LLM error)
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        
        # Fix single quotes around strings
        json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
        
        # Fix missing quotes around string values
        json_str = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_\s]*)\s*([,}])', r': "\1"\2', json_str)
        
        # Fix boolean values to lowercase
        json_str = re.sub(r'\bTrue\b', 'true', json_str)
        json_str = re.sub(r'\bFalse\b', 'false', json_str)
        json_str = re.sub(r'\bNone\b', 'null', json_str)
        
        return json_str

    def _extract_partial_json(self, text: str) -> str:
        """
        Extract partial valid JSON by finding key structures
        """
        import re
        
        # Look for the open_codes array specifically
        open_codes_match = re.search(r'"open_codes"\s*:\s*\[(.*?)\]', text, re.DOTALL)
        if open_codes_match:
            codes_content = open_codes_match.group(1)
            
            # Try to build a minimal valid structure
            return f'{{"open_codes": [{codes_content}]}}'
        
        # Fallback: return minimal valid structure
        return '{"open_codes": []}'

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from text that might contain other content
        
        Looks for JSON blocks in various formats:
        - ```json ... ```
        - { ... }
        - [ ... ]
        """
        import re
        
        # Try to find JSON in code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # Try to find raw JSON object or array
            json_pattern = r'(\{.*\}|\[.*\])'
            match = re.search(json_pattern, text, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                raise ValueError("No JSON found in response")
        
        # Parse the extracted JSON
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            if "Extra data" in str(e):
                # Try to extract only the valid JSON portion when there's extra data
                try:
                    # Find the first complete JSON object
                    decoder = json.JSONDecoder()
                    obj, idx = decoder.raw_decode(json_str)
                    return obj
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # Try to fix common JSON issues
            json_str = self._fix_json_string(json_str)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e2:
                if "Extra data" in str(e2):
                    # Try raw decode again after fixing
                    try:
                        decoder = json.JSONDecoder()
                        obj, idx = decoder.raw_decode(json_str)
                        return obj
                    except (json.JSONDecodeError, ValueError):
                        pass
                raise e2
    
    async def _retry_without_json_mode(
        self,
        prompt: str,
        schema: Type[BaseModel],
        instructions: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> BaseModel:
        """
        Retry structured extraction without JSON mode when JSON mode fails
        
        This is a fallback for cases where JSON mode returns None responses
        (common with very large prompts or certain prompt formats)
        """
        # Build the full prompt with explicit JSON request
        full_prompt = self._build_extraction_prompt(prompt, schema, instructions)
        full_prompt += "\n\nIMPORTANT: Return ONLY a valid JSON object, nothing else."
        
        # Prepare messages for LLM without JSON mode
        messages = [
            {
                "role": "system", 
                "content": "You are an expert at extracting structured information from text. "
                          "Return your response as valid JSON that matches the provided schema. "
                          "Do not include any text before or after the JSON object."
            },
            {
                "role": "user",
                "content": full_prompt
            }
        ]
        
        try:
            # Build kwargs without JSON mode
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature
            }
            
            # Add max_tokens if available
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            elif self.default_max_tokens is not None:
                kwargs["max_tokens"] = self.default_max_tokens
            
            logger.info(f"Retrying without JSON mode, max_tokens: {kwargs.get('max_tokens', 'unlimited')}")
            
            # Call LiteLLM without JSON mode
            response = await litellm.acompletion(**kwargs)
            
            # Extract content
            if hasattr(response, 'choices') and response.choices:
                response_content = response.choices[0].message.content
                
                if response_content is None:
                    raise ValueError("Still received None response even without JSON mode")
                
                if isinstance(response_content, str):
                    # Extract JSON from text response
                    try:
                        response_data = json.loads(response_content)
                    except json.JSONDecodeError:
                        logger.info("Direct JSON parsing failed, attempting pattern extraction with fixing")
                        response_data = self._extract_and_fix_json_from_text(response_content)
                    
                    # Create and validate model instance
                    model_instance = schema(**response_data)
                    logger.info(f"Successfully extracted {schema.__name__} using fallback mode")
                    return model_instance
                else:
                    raise ValueError(f"Unexpected response content type in fallback: {type(response_content)}")
            else:
                raise ValueError("No valid response content found in fallback mode")
                
        except Exception as e:
            logger.error(f"Fallback mode also failed: {e}")
            raise LLMError(f"Failed to extract {schema.__name__} even with fallback: {e}") from e

    def _fix_json_string(self, json_str: str) -> str:
        """
        Attempt to fix common JSON formatting issues
        """
        import re
        
        # Remove trailing commas before closing brackets
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # Fix missing commas between objects (common LLM error)
        # Look for patterns like "}  {" and replace with "}, {"
        json_str = re.sub(r'}\s*{', '}, {', json_str)
        
        # Fix missing commas between array elements
        # Look for patterns like "]  [" and replace with "], ["  
        json_str = re.sub(r']\s*\[', '], [', json_str)
        
        # Fix missing commas after values before new keys
        # Look for patterns like '"value"  "key"' and replace with '"value", "key"'
        json_str = re.sub(r'"\s*"([^"]*)":', '", "$1":', json_str)
        
        # Remove comments (if any)
        json_str = re.sub(r'//.*?\n', '', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # Remove any markdown code block markers that might have been included
        json_str = re.sub(r'```(?:json)?\s*', '', json_str)
        json_str = re.sub(r'```\s*$', '', json_str)
        
        return json_str
    
    async def complete_raw(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Raw completion without structured extraction with retry logic
        
        Args:
            prompt: The prompt to complete
            max_tokens: Maximum tokens (None = use maximum available)
            temperature: Temperature override
        
        Returns:
            Raw text response
        """
        
        async def _complete_operation():
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature or self.temperature,
                # Remove timeout limit
            }
            
            # Only add max_tokens if explicitly provided or configured
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            elif self.default_max_tokens is not None:
                kwargs["max_tokens"] = self.default_max_tokens
            
            response = await litellm.acompletion(**kwargs)
            
            if not response or not response.choices:
                raise Exception("Empty response from LLM API")
                
            content = response.choices[0].message.content
            if not content:
                raise Exception("Empty content in LLM response")
                
            return content.strip()
        
        try:
            return await self._retry_with_backoff(
                _complete_operation,
                "complete_raw"
            )
        except Exception as e:
            logger.error(f"Raw completion failed: {e}")
            raise LLMError(f"Raw completion failed: {e}") from e


# Import for compatibility
import re