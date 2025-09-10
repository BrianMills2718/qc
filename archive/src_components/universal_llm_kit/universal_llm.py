"""
Universal LLM Interface - Drop into any project
Handles all major providers with automatic optimization
"""

import os
import litellm
from litellm import Router
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Suppress LiteLLM logs for cleaner output
litellm.suppress_debug_info = True


class UniversalLLM:
    """Universal interface for all LLM providers with smart routing"""
    
    def __init__(self):
        self.router = self._setup_router()
    
    def _setup_router(self) -> Router:
        """Setup router with all available models and fallbacks"""
        model_list = []
        
        # OpenAI Models (if API key available)
        if os.getenv("OPENAI_API_KEY"):
            model_list.extend([
                {"model_name": "smart", "litellm_params": {"model": "gpt-4o", "max_tokens": 4096}},
                {"model_name": "reasoning", "litellm_params": {"model": "o1-preview", "max_completion_tokens": 32768}},
                {"model_name": "fast", "litellm_params": {"model": "gpt-4o-mini", "max_tokens": 16384}},
            ])
        
        # Anthropic Models (if API key available)  
        if os.getenv("ANTHROPIC_API_KEY"):
            model_list.extend([
                {"model_name": "smart", "litellm_params": {"model": "claude-3-5-sonnet-20241022", "max_tokens": 8192}},
                {"model_name": "fast", "litellm_params": {"model": "claude-3-5-haiku-20241022", "max_tokens": 8192}},
            ])
        
        # Google Models (if API key available)
        if os.getenv("GEMINI_API_KEY"):
            model_list.extend([
                {"model_name": "code", "litellm_params": {"model": "gemini/gemini-2.5-flash", "max_tokens": 65536, "tools": [{"codeExecution": {}}]}},
                {"model_name": "smart", "litellm_params": {"model": "gemini/gemini-2.0-flash", "max_tokens": 65536}},
                {"model_name": "thinking", "litellm_params": {"model": "gemini/gemini-2.0-flash-thinking", "max_tokens": 32768}},
            ])
        
        # OpenRouter (if API key available)
        if os.getenv("OPENROUTER_API_KEY"):
            model_list.extend([
                {"model_name": "smart", "litellm_params": {"model": "openrouter/anthropic/claude-3.5-sonnet", "max_tokens": 8192}},
                {"model_name": "fast", "litellm_params": {"model": "openrouter/meta-llama/llama-3.1-8b-instruct:free", "max_tokens": 8192}},
            ])
        
        if not model_list:
            raise ValueError("No API keys found! Please set at least one API key in .env file")
        
        return Router(
            model_list=model_list,
            routing_strategy="cost-based",  # Use cheapest available model
            fallbacks=["smart", "fast", "code", "reasoning", "thinking"]
        )
    
    def chat(self, prompt: str, model_type: str = "smart", **kwargs) -> str:
        """Universal chat interface"""
        response = self.router.completion(
            model=model_type,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content
    
    def code_execution(self, prompt: str) -> str:
        """Execute code using Gemini's native code execution"""
        try:
            return self.chat(prompt, model_type="code")
        except Exception as e:
            # Fallback to regular model if code execution fails
            return self.chat(f"Please solve this step by step with detailed explanation: {prompt}", model_type="smart")
    
    def reasoning(self, prompt: str) -> str:
        """Use o1 models for complex reasoning"""
        try:
            return self.chat(prompt, model_type="reasoning")
        except Exception as e:
            # Fallback to regular model
            return self.chat(f"Think through this step by step: {prompt}", model_type="smart")
    
    def function_call(self, prompt: str, functions: List[Dict]) -> Any:
        """Universal function calling"""
        response = self.router.completion(
            model="smart",
            messages=[{"role": "user", "content": prompt}],
            tools=functions
        )
        return response
    
    def structured_output(self, prompt: str, schema: Optional[BaseModel] = None) -> str:
        """
        Get structured JSON output using conservative approach
        
        NOTE: This uses basic JSON mode for maximum compatibility across all models.
        For production systems, use direct LiteLLM with Pydantic models instead:
        
            import litellm
            response = litellm.completion(
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                response_format=schema  # ← Direct Pydantic model
            )
        
        This provides true schema enforcement vs. prompt-based JSON generation.
        """
        kwargs = {}
        if schema:
            kwargs["response_format"] = {"type": "json_object"}
            prompt = f"{prompt}\n\nRespond with valid JSON matching this schema: {schema.model_json_schema()}"
        else:
            kwargs["response_format"] = {"type": "json_object"}
            prompt = f"{prompt}\n\nRespond with valid JSON."
        
        return self.chat(prompt, **kwargs)
    
    def compare_models(self, prompt: str, models: List[str] = None) -> Dict[str, str]:
        """Compare responses across different models"""
        if models is None:
            models = ["smart", "fast", "code"]
        
        results = {}
        for model in models:
            try:
                results[model] = self.chat(prompt, model_type=model)
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
    print(f"Available models: {[m['model_name'] for m in llm.router.model_list]}")