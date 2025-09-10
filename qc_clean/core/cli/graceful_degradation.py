#!/usr/bin/env python3
"""
Graceful Degradation System for Qualitative Coding Analysis Tool

Provides systematic fallback mechanisms and graceful degradation for various
system components when dependencies are unavailable or operations fail.
"""

import logging
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Callable, TypeVar
from functools import wraps
from contextlib import contextmanager
from enum import Enum
from datetime import datetime

from ..utils.error_handler import (
    LLMError, TokenLimitError, RateLimitError, ValidationError, 
    ProcessingError, QueryError
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DegradationLevel(Enum):
    """Levels of system degradation"""
    FULL = "full"           # Full functionality available
    LIMITED = "limited"     # Some features disabled
    ESSENTIAL = "essential" # Only essential features
    EMERGENCY = "emergency" # Minimal functionality


class SystemCapability:
    """Represents a system capability and its fallback strategies"""
    
    def __init__(self, name: str, required: bool = False, fallback: Optional[str] = None):
        self.name = name
        self.required = required
        self.fallback = fallback
        self.available = True
        self.error_count = 0
        self.last_error = None


class FailFastManager:
    """
    Manages fail-fast behavior for system capabilities. When critical
    dependencies fail, the system fails immediately with clear error messages.
    """
    
    def __init__(self):
        self.capabilities = self._initialize_capabilities()
        self.system_status = DegradationLevel.FULL
        self.system_errors = []
        self.fail_fast_mode = True
    
    def _initialize_capabilities(self) -> Dict[str, SystemCapability]:
        """Initialize system capabilities - all marked as required for fail-fast"""
        return {
            # Core capabilities - all required for fail-fast
            'llm_api': SystemCapability('llm_api', required=True),
            'file_access': SystemCapability('file_access', required=True),
            'basic_processing': SystemCapability('basic_processing', required=True),
            
            # Optional capabilities - will warn but not fail
            'neo4j_database': SystemCapability('neo4j_database', required=False),
            'web_interface': SystemCapability('web_interface', required=False),
            'export_functionality': SystemCapability('export_functionality', required=True),
            'network_connectivity': SystemCapability('network_connectivity', required=False),
        }
    
    def _get_critical_capabilities(self) -> List[str]:
        """Get list of critical capabilities that must work"""
        return [name for name, cap in self.capabilities.items() if cap.required]
    
    def assess_system_health(self) -> DegradationLevel:
        """Assess system health - fail fast if critical capabilities down"""
        critical_failures = []
        optional_failures = []
        
        for name, cap in self.capabilities.items():
            if not cap.available:
                if cap.required:
                    critical_failures.append(name)
                else:
                    optional_failures.append(name)
        
        if critical_failures:
            # In fail-fast mode, any critical failure = system failure
            self.system_status = DegradationLevel.EMERGENCY
            error_msg = f"CRITICAL FAILURE: Required capabilities unavailable: {', '.join(critical_failures)}"
            logger.critical(error_msg)
            raise ProcessingError(error_msg)
        elif optional_failures:
            self.system_status = DegradationLevel.LIMITED
            logger.warning(f"Optional capabilities unavailable: {', '.join(optional_failures)}")
        else:
            self.system_status = DegradationLevel.FULL
        
        logger.info(f"System status: {self.system_status.value}")
        return self.system_status
    
    def mark_capability_failed(self, capability_name: str, error: Exception):
        """Mark a capability as failed - fail fast if critical"""
        if capability_name not in self.capabilities:
            logger.warning(f"Unknown capability marked as failed: {capability_name}")
            return
        
        cap = self.capabilities[capability_name]
        cap.available = False
        cap.error_count += 1
        cap.last_error = str(error)
        
        # Record error for reporting
        self.system_errors.append({
            'capability': capability_name,
            'error': str(error),
            'timestamp': datetime.now().isoformat(),
            'required': cap.required
        })
        
        if cap.required:
            # Critical capability failed - fail fast
            error_msg = f"CRITICAL: Required capability '{capability_name}' failed: {error}"
            logger.critical(error_msg)
            raise ProcessingError(error_msg)
        else:
            # Optional capability failed - warn but continue
            logger.warning(f"Optional capability '{capability_name}' failed: {error}")
            logger.info(f"System will continue without '{capability_name}' functionality")
        
        # Update system status
        self.assess_system_health()
    
    def is_capability_available(self, capability_name: str) -> bool:
        """Check if a capability is available"""
        return self.capabilities.get(capability_name, SystemCapability(capability_name)).available
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'system_status': self.system_status.value,
            'fail_fast_mode': self.fail_fast_mode,
            'capabilities': {
                name: {
                    'available': cap.available,
                    'required': cap.required,
                    'error_count': cap.error_count,
                    'last_error': cap.last_error
                }
                for name, cap in self.capabilities.items()
            },
            'system_errors': self.system_errors[-10:],  # Last 10 errors
        }
    
    @contextmanager
    def capability_context(self, capability_name: str):
        """Context manager for capability-dependent operations"""
        if not self.is_capability_available(capability_name):
            yield False
            return
        
        try:
            yield True
        except Exception as e:
            self.mark_capability_failed(capability_name, e)
            raise
    
# Global fail-fast manager instance
fail_fast_manager = FailFastManager()


def with_fail_fast(capability: str, error_message: str = None):
    """
    Decorator for functions that should fail fast when capabilities are unavailable.
    
    Args:
        capability: Name of the required capability
        error_message: Custom error message to show on failure
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # Check if capability is available before executing
            if not fail_fast_manager.is_capability_available(capability):
                error_msg = error_message or f"Required capability '{capability}' is unavailable"
                logger.error(f"Blocking {func.__name__}: {error_msg}")
                raise ProcessingError(error_msg)
                
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Mark capability as failed and re-raise the error
                fail_fast_manager.mark_capability_failed(capability, e)
                raise  # Re-raise original error for fail-fast behavior
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # Check if capability is available before executing
            if not fail_fast_manager.is_capability_available(capability):
                error_msg = error_message or f"Required capability '{capability}' is unavailable"
                logger.error(f"Blocking {func.__name__}: {error_msg}")
                raise ProcessingError(error_msg)
                
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Mark capability as failed and re-raise the error
                fail_fast_manager.mark_capability_failed(capability, e)
                raise  # Re-raise original error for fail-fast behavior
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def ensure_essential_functionality() -> bool:
    """
    Ensure essential system functionality is available.
    In fail-fast mode, this will raise an exception if critical capabilities fail.
    """
    try:
        # This will raise ProcessingError if any critical capability fails
        fail_fast_manager.assess_system_health()
        return True
    except ProcessingError as e:
        # Log the critical failure and return False to indicate shutdown needed
        logger.critical(f"System cannot continue: {e}")
        return False


class FailFastFileHandler:
    """File handling with fail-fast error behavior"""
    
    @staticmethod
    @with_fail_fast('file_access', "File system access required but unavailable")
    def safe_read_text(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Safely read text file with encoding fallbacks"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Try primary encoding
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            # Fallback encodings
            fallback_encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
            
            for fallback_encoding in fallback_encodings:
                if fallback_encoding == encoding:
                    continue
                
                try:
                    logger.warning(f"Retrying with encoding: {fallback_encoding}")
                    return path.read_text(encoding=fallback_encoding)
                except UnicodeDecodeError:
                    continue
            
            # Final fallback - read as binary and decode with errors='replace'
            logger.warning("Using binary read with error replacement")
            return path.read_text(encoding='utf-8', errors='replace')
    
    @staticmethod
    @with_fail_fast('file_access', "File system write access required but unavailable")
    def safe_write_text(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """Safely write text file with error handling"""
        path = Path(file_path)
        
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            path.write_text(content, encoding=encoding)
            return True
            
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            raise ProcessingError(f"Failed to write file {file_path}: {e}")
    
    @staticmethod
    @with_fail_fast('basic_processing', "JSON processing required but unavailable")
    def safe_read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Safely read JSON file with error handling"""
        try:
            text_content = FailFastFileHandler.safe_read_text(file_path)
            if not text_content.strip():
                logger.warning(f"Empty JSON file: {file_path}")
                return {}
            
            return json.loads(text_content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
            raise ProcessingError(f"Invalid JSON in {file_path}: {e}")
    
    @staticmethod
    @with_fail_fast('basic_processing', "JSON processing required but unavailable")
    def safe_write_json(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> bool:
        """Safely write JSON file with error handling"""
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            return FailFastFileHandler.safe_write_text(file_path, content)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON serialization error for {file_path}: {e}")
            raise ProcessingError(f"JSON serialization failed for {file_path}: {e}")


class FailFastNetworkHandler:
    """Network operations with fail-fast behavior"""
    
    @staticmethod
    @with_fail_fast('network_connectivity', "Network connectivity required but unavailable")
    def check_connectivity() -> bool:
        """Check basic network connectivity"""
        try:
            import urllib.request
            urllib.request.urlopen('http://google.com')
            return True
        except Exception as e:
            logger.error(f"Network connectivity check failed: {e}")
            raise ProcessingError(f"No network connectivity: {e}")
    
    @staticmethod
    @with_fail_fast('llm_api', "LLM API access required but unavailable")
    async def safe_llm_call(llm_handler, prompt: str, **kwargs) -> str:
        """Make LLM API call with fail-fast behavior"""
        try:
            result = await llm_handler.generate(prompt, **kwargs)
            if not result:
                raise ProcessingError("LLM API returned empty response")
            return result
        except (RateLimitError, TokenLimitError) as e:
            logger.error(f"LLM API error: {e}")
            raise ProcessingError(f"LLM API failed: {e}")
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise ProcessingError(f"LLM API failed: {e}")