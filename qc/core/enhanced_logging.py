"""
Enhanced logging for debugging LLM calls
"""
import logging
import time
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMCallLogger:
    """Log detailed information about LLM calls for debugging."""
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path("debug_llm_calls")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def log_call_start(self, call_id: str, prompt: str, config: Dict[str, Any]) -> float:
        """Log the start of an LLM call."""
        start_time = time.time()
        
        # Log to file
        log_data = {
            "call_id": call_id,
            "timestamp": datetime.now().isoformat(),
            "start_time": start_time,
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "config": config,
            "status": "started"
        }
        
        log_file = self.log_dir / f"{call_id}_start.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        
        # Log to console
        logger.info(f"LLM Call {call_id} started:")
        logger.info(f"  - Prompt length: {len(prompt)} chars")
        logger.info(f"  - Max output tokens: {config.get('max_output_tokens', 'default')}")
        logger.info(f"  - Temperature: {config.get('temperature', 'default')}")
        
        return start_time
    
    def log_call_end(self, call_id: str, start_time: float, response: Any, 
                     success: bool = True, error: Optional[str] = None):
        """Log the end of an LLM call."""
        end_time = time.time()
        duration = end_time - start_time
        
        # Determine response info
        if isinstance(response, str):
            response_info = {
                "type": "string",
                "length": len(response),
                "preview": response[:500] + "..." if len(response) > 500 else response
            }
        elif isinstance(response, dict):
            response_info = {
                "type": "dict",
                "keys": list(response.keys()),
                "size": len(json.dumps(response))
            }
        else:
            response_info = {
                "type": type(response).__name__,
                "repr": repr(response)[:500]
            }
        
        # Log to file
        log_data = {
            "call_id": call_id,
            "timestamp": datetime.now().isoformat(),
            "end_time": end_time,
            "duration_seconds": duration,
            "success": success,
            "error": error,
            "response_info": response_info,
            "status": "completed" if success else "failed"
        }
        
        log_file = self.log_dir / f"{call_id}_end.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        
        # Log to console
        if success:
            logger.info(f"LLM Call {call_id} completed in {duration:.1f}s")
            logger.info(f"  - Response type: {response_info['type']}")
            if 'length' in response_info:
                logger.info(f"  - Response length: {response_info['length']} chars")
        else:
            logger.error(f"LLM Call {call_id} FAILED after {duration:.1f}s")
            logger.error(f"  - Error: {error}")
    
    def log_progress(self, call_id: str, message: str):
        """Log progress during a long-running call."""
        logger.info(f"LLM Call {call_id} progress: {message}")
    
    def save_full_response(self, call_id: str, response: Any):
        """Save the full response for detailed debugging."""
        response_file = self.log_dir / f"{call_id}_full_response.txt"
        
        if isinstance(response, str):
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(response)
        else:
            with open(response_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2, default=str)
        
        logger.info(f"Full response saved to {response_file}")


# Global logger instance
llm_logger = LLMCallLogger()