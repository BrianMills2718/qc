"""
Hybrid Gemini Client with LiteLLM Integration
- Structured Output: Uses LiteLLM for consistent schema enforcement across providers
- Text Generation: Uses native google.generativeai for compatibility with existing code
- Configured for academic research with appropriate safety settings
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
from ..utils.error_handler import LLMError, LiteLLMError, LiteLLMSchemaError

logger = logging.getLogger(__name__)

# Load environment variables from .env file
# GEMINI_API_KEY=AIzaSyDXaLhSWAQhGNHZqdbvY-qFB0jxyPbiiow (confirmed present in .env)
load_dotenv()

class NativeGeminiClient:
    """Hybrid Gemini client: LiteLLM structured output + native text generation for academic research"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure the client
        genai.configure(api_key=self.api_key)
        
        # Configure safety settings for academic research
        # These settings allow academic research content that might otherwise be blocked
        self.safety_settings = [
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            }
        ]
        
        logger.info("Native Gemini client configured with academic research safety settings")
        
        # Debug mode for troubleshooting safety issues
        self.debug_mode = os.getenv("GEMINI_DEBUG_MODE", "false").lower() == "true"
    
    # Legacy schema cleaning methods removed - LiteLLM handles schema conversion automatically
    
    def structured_output(self, 
                         prompt: str, 
                         schema: Type[BaseModel],
                         model: str = "gemini-2.5-flash") -> Dict[str, Any]:
        """
        Generate structured output using LiteLLM with direct Pydantic support
        
        MIGRATION NOTE: Replaced native Gemini implementation with LiteLLM
        for better schema enforcement and multi-provider compatibility.
        
        Args:
            prompt: The prompt to send to the model
            schema: Pydantic model defining the expected output structure
            model: Gemini model to use (will be converted to LiteLLM format)
            
        Returns:
            Dict containing the structured response
        """
        try:
            import litellm
            
            # Convert model name to LiteLLM format
            litellm_model = f"gemini/{model}" if not model.startswith("gemini/") else model
            
            if self.debug_mode:
                logger.info(f"LiteLLM structured output: {litellm_model}")
                logger.info(f"Schema: {schema.__name__}")
                logger.info(f"Prompt: {prompt[:200]}...")
            
            # Use LiteLLM with direct Pydantic model support
            response = litellm.completion(
                model=litellm_model,
                messages=[{"role": "user", "content": prompt}],
                response_format=schema  # ← Direct Pydantic model - real schema enforcement!
            )
            
            # Extract and parse the response
            raw_response = response.choices[0].message.content
            result = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
            
            if self.debug_mode:
                logger.info(f"LiteLLM response received: {len(str(result))} chars")
            
            return {
                'response': result,
                'raw_text': raw_response,
                'model_used': litellm_model,
                'success': True,
                'method': 'litellm_structured'
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed in LiteLLM structured generation: {e}")
            raise LiteLLMError(f"LiteLLM JSON parsing failed: {e}") from e
        except Exception as e:
            error_str = str(e)
            logger.error(f"LiteLLM generation failed: {e}")
            
            # Log more details for debugging
            if hasattr(e, '__dict__'):
                logger.error(f"Error details: {e.__dict__}")
            
            # Classify LiteLLM-specific errors
            if 'response_schema' in error_str or 'schema' in error_str:
                raise LiteLLMSchemaError(f"Schema validation failed: {e}") from e
            elif 'litellm.BadRequestError' in str(type(e)):
                raise LiteLLMError(f"LiteLLM bad request: {e}") from e  
            elif 'litellm.RateLimitError' in str(type(e)):
                raise LiteLLMError(f"LiteLLM rate limit: {e}") from e
            elif 'litellm' in error_str.lower():
                raise LiteLLMError(f"LiteLLM error: {e}") from e
            else:
                raise LLMError(f"LiteLLM generation failed: {e}") from e
    
    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1, model: str = "gemini-2.5-flash") -> str:
        """
        Generate text response - async method expected by SemanticCodeMatcher
        
        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens to generate (Note: Gemini uses max_output_tokens)
            temperature: Temperature for generation
            model: Model name to use
            
        Returns:
            Generated text response
        """
        try:
            if self.debug_mode:
                logger.info(f"DEBUG: Sending prompt to Gemini: {prompt[:500]}...")
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=min(max_tokens, 8192)  # Gemini limit
            )
            
            model_obj = genai.GenerativeModel(
                model, 
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            response = model_obj.generate_content(
                prompt,
                safety_settings=self.safety_settings
            )
            
            # Check for safety filtering
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    if candidate.finish_reason == 2:  # SAFETY
                        safety_ratings = getattr(candidate, 'safety_ratings', [])
                        safety_info = []
                        for rating in safety_ratings:
                            safety_info.append(f"{rating.category}: {rating.probability}")
                        
                        error_msg = f"Content blocked by safety filter. Ratings: {', '.join(safety_info)}"
                        logger.error(error_msg)
                        
                        if self.debug_mode:
                            logger.error(f"DEBUG: Blocked prompt was: {prompt}")
                        
                        raise LLMError(f"Safety filter blocked content: {error_msg}")
            
            return response.text
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            
            # Additional debugging for safety issues
            if "finish_reason" in str(e) and "2" in str(e):
                logger.error("SAFETY FILTER TRIGGERED - Content blocked by Gemini safety system")
                if self.debug_mode:
                    logger.error(f"DEBUG: Blocked prompt: {prompt}")
            
            raise LLMError(f"Generation failed: {str(e)}")

    def chat(self, prompt: str, model: str = "gemini-2.5-flash") -> str:
        """Simple chat without structured output - uses native Gemini API"""
        try:
            model_obj = genai.GenerativeModel(model, safety_settings=self.safety_settings)
            response = model_obj.generate_content(
                prompt,
                safety_settings=self.safety_settings
            )
            return response.text
        except Exception as e:
            raise Exception(f"Chat generation failed: {str(e)}")
    
    def complete(self, messages: List[Dict], schema: Optional[Type[BaseModel]] = None, **kwargs) -> Dict[str, Any]:
        """
        Compatibility method for existing code
        Converts messages to single prompt and uses structured output if schema provided
        """
        # Convert messages to single prompt
        if isinstance(messages, list) and messages:
            if len(messages) == 1:
                prompt = messages[0].get('content', str(messages[0]))
            else:
                # Combine multiple messages
                prompt = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', str(msg))}" 
                    for msg in messages
                ])
        else:
            prompt = str(messages)
        
        if schema:
            return self.structured_output(prompt, schema)
        else:
            try:
                response_text = self.chat(prompt)
                return {
                    'response': response_text,
                    'model_used': 'gemini-2.5-flash',
                    'success': True,
                    'method': 'native_gemini_chat'
                }
            except Exception as e:
                logger.error(f"Gemini chat generation failed: {e}")
                raise LLMError(f"Gemini chat generation failed: {e}") from e

# Mock response class for compatibility
class MockResponse:
    def __init__(self, content):
        if isinstance(content, dict):
            self.content = json.dumps(content)
        else:
            self.content = str(content)

if __name__ == "__main__":
    # Quick test
    from pydantic import BaseModel
    
    class TestSchema(BaseModel):
        message: str
        count: int
    
    client = NativeGeminiClient()
    print("🚀 Native Gemini Client ready!")
    
    # Test structured output
    result = client.structured_output(
        "Create a test message with count 42", 
        TestSchema
    )
    print(f"Test result: {result}")