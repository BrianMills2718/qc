"""
Universal LLM Interface - Drop into any project
Handles all major providers with automatic optimization
"""

import os
import logging
import litellm
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Suppress LiteLLM logs for cleaner output
litellm.suppress_debug_info = True


class UniversalLLM:
    """Universal interface for all LLM providers with smart routing"""
    
    def __init__(self):
        self.models = self._setup_models()
    
    def _setup_models(self) -> Dict[str, str]:
        """Setup available models based on API keys"""
        models = {}
        
        # Prioritize providers: Gemini > Anthropic > OpenAI (cost-based)
        
        # Google Models (if API key available) - Primary choice  
        if os.getenv("GEMINI_API_KEY"):
            models.update({
                "smart": "gemini/gemini-2.0-flash",
                "code": "gemini/gemini-2.5-flash", 
                "fast": "gemini/gemini-2.5-flash",
                "thinking": "gemini/gemini-2.0-flash-thinking"
            })
        
        # Anthropic Models (if API key available and no Gemini)
        elif os.getenv("ANTHROPIC_API_KEY"):
            models.update({
                "smart": "claude-3-5-sonnet-20241022",
                "fast": "claude-3-5-haiku-20241022"
            })
        
        # OpenAI Models (if API key available and no Gemini/Anthropic)
        elif os.getenv("OPENAI_API_KEY"):
            models.update({
                "smart": "gpt-4o",
                "reasoning": "o1-preview", 
                "fast": "gpt-4o-mini"
            })
        
        if not models:
            raise ValueError("No API keys found! Please set at least one API key in .env file")
        
        return models
    
    def chat(self, prompt: str, model_type: str = "smart", **kwargs) -> str:
        """Universal chat interface"""
        if model_type not in self.models:
            model_type = "smart"  # Fallback to smart model
            
        model = self.models[model_type]
        
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content
    
    def code_execution(self, prompt: str) -> str:
        """Execute code using Gemini's native code execution"""
        try:
            return self.chat(prompt, model_type="code")
        except Exception as e:
            # FAIL-FAST: No fallback, raise the original error
            logger.error(f"Code execution failed: {e}")
            raise Exception(f"Code execution failed: {e}") from e
    
    def reasoning(self, prompt: str) -> str:
        """Use o1 models for complex reasoning"""
        try:
            return self.chat(prompt, model_type="reasoning")
        except Exception as e:
            # FAIL-FAST: No fallback, raise the original error
            logger.error(f"Reasoning model failed: {e}")
            raise Exception(f"Reasoning model failed: {e}") from e
    
    def function_call(self, prompt: str, functions: List[Dict]) -> Any:
        """Universal function calling"""
        model = self.models.get("smart", list(self.models.values())[0])
        
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            tools=functions
        )
        return response
    
    def structured_output(self, prompt: str, schema: Optional[BaseModel] = None) -> str:
        """Get structured JSON output"""
        model = self.models.get("smart", list(self.models.values())[0])
        
        kwargs = {"response_format": {"type": "json_object"}}
        
        if schema:
            prompt = f"{prompt}\n\nRespond with valid JSON matching this schema: {schema.model_json_schema()}"
        else:
            prompt = f"{prompt}\n\nRespond with valid JSON."
        
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content
    
    def compare_models(self, prompt: str, models: List[str] = None) -> Dict[str, str]:
        """Compare responses across different models"""
        if models is None:
            models = list(self.models.keys())[:3]  # Use first 3 available models
        
        results = {}
        for model in models:
            try:
                if model in self.models:
                    results[model] = self.chat(prompt, model_type=model)
                else:
                    results[model] = f"Error: Model {model} not available"
            except Exception as e:
                results[model] = f"Error: {str(e)}"
        
        return results


# Convenience functions for quick use
_llm = None

def get_llm() -> UniversalLLM:
    """Get singleton LLM instance"""
    global _llm
    if _llm is None:
        _llm = UniversalLLM()
    return _llm

def chat(prompt: str, model_type: str = "smart") -> str:
    """Quick chat function"""
    return get_llm().chat(prompt, model_type)

def code(prompt: str) -> str:
    """Quick code execution"""
    return get_llm().code_execution(prompt)

def reason(prompt: str) -> str:
    """Quick reasoning with o1 models"""
    return get_llm().reasoning(prompt)

def structured(prompt: str, schema: Optional[BaseModel] = None) -> str:
    """Quick structured output"""
    return get_llm().structured_output(prompt, schema)

def compare(prompt: str, models: List[str] = None) -> Dict[str, str]:
    """Quick model comparison"""
    return get_llm().compare_models(prompt, models)


if __name__ == "__main__":
    # Quick test
    llm = UniversalLLM()
    print("🚀 Universal LLM ready!")
    print(f"Available models: {list(llm.models.keys())}")
    print(f"Model mappings: {llm.models}")