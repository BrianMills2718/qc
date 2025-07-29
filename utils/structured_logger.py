#!/usr/bin/env python3
"""
Structured Logging System with Correlation IDs
Provides JSON-formatted logs with request tracing across the entire application
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from pythonjsonlogger import jsonlogger
import traceback
from functools import wraps
import asyncio

# Context variables for correlation tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds correlation IDs and metadata to all log records.
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        """Add custom fields to the log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        
        # Add correlation IDs from context
        log_record['correlation_id'] = correlation_id_var.get()
        log_record['request_id'] = request_id_var.get()
        log_record['session_id'] = session_id_var.get()
        log_record['user_id'] = user_id_var.get()
        
        # Add location information
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add level as both name and number for filtering
        log_record['level'] = record.levelname
        log_record['level_number'] = record.levelno
        
        # Add process and thread info for debugging
        log_record['process'] = record.process
        log_record['thread'] = record.thread
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
            log_record['exception_type'] = record.exc_info[0].__name__ if record.exc_info[0] else None
        
        # Remove None values for cleaner logs
        log_record = {k: v for k, v in log_record.items() if v is not None}


class CorrelationFilter(logging.Filter):
    """
    Filter that ensures correlation IDs are present in log records.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation IDs to the record."""
        record.correlation_id = correlation_id_var.get() or 'no-correlation'
        record.request_id = request_id_var.get() or 'no-request'
        record.session_id = session_id_var.get() or 'no-session'
        record.user_id = user_id_var.get() or 'anonymous'
        return True


class StructuredLogger:
    """
    Main logger class that provides structured logging capabilities.
    """
    
    def __init__(self, name: str, level: str = "INFO"):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually __name__)
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # Create JSON formatter
        formatter = StructuredFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            timestamp=True
        )
        
        # Console handler with JSON output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(CorrelationFilter())
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
    
    def _log_with_context(self, level: str, message: str, **kwargs):
        """
        Log with additional context fields.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional fields to include in the log
        """
        # Add performance metrics if available
        if 'duration_ms' in kwargs:
            kwargs['duration_ms'] = round(kwargs['duration_ms'], 2)
        
        # Get the appropriate logging method
        log_method = getattr(self.logger, level.lower())
        
        # Log with extra fields
        log_method(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context('debug', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self._log_with_context('error', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self._log_with_context('critical', message, **kwargs)
    
    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """
        Log performance metrics.
        
        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            **kwargs: Additional metrics
        """
        self.info(
            f"Performance metric: {operation}",
            operation=operation,
            duration_ms=duration_ms,
            metric_type='performance',
            **kwargs
        )
    
    def log_api_request(self, method: str, path: str, status_code: int, 
                       duration_ms: float, **kwargs):
        """
        Log API request with standard fields.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration
            **kwargs: Additional fields
        """
        self.info(
            f"{method} {path} - {status_code}",
            http_method=method,
            http_path=path,
            http_status=status_code,
            duration_ms=duration_ms,
            event_type='api_request',
            **kwargs
        )
    
    def log_database_query(self, query: str, duration_ms: float, 
                          rows_affected: Optional[int] = None, **kwargs):
        """
        Log database query execution.
        
        Args:
            query: SQL query (sanitized)
            duration_ms: Query execution time
            rows_affected: Number of rows affected
            **kwargs: Additional fields
        """
        # Truncate long queries
        display_query = query[:200] + '...' if len(query) > 200 else query
        
        self.info(
            f"Database query executed",
            query=display_query,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            event_type='database_query',
            **kwargs
        )
    
    def log_llm_call(self, model: str, operation: str, tokens_in: int, 
                     tokens_out: int, duration_ms: float, **kwargs):
        """
        Log LLM API call.
        
        Args:
            model: Model name
            operation: Operation type
            tokens_in: Input tokens
            tokens_out: Output tokens
            duration_ms: Call duration
            **kwargs: Additional fields
        """
        self.info(
            f"LLM call: {model} - {operation}",
            llm_model=model,
            llm_operation=operation,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            duration_ms=duration_ms,
            event_type='llm_call',
            **kwargs
        )
    
    def log_exception(self, message: str, exc: Exception, **kwargs):
        """
        Log exception with full context.
        
        Args:
            message: Error message
            exc: Exception object
            **kwargs: Additional context
        """
        self.error(
            message,
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            exception_traceback=traceback.format_exc(),
            event_type='exception',
            **kwargs
        )


# Correlation ID Management
def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return f"corr_{uuid.uuid4().hex[:12]}"


def generate_request_id() -> str:
    """Generate a new request ID."""
    return f"req_{uuid.uuid4().hex[:12]}"


def set_correlation_context(
    correlation_id: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    Set correlation context for the current execution.
    
    Args:
        correlation_id: Correlation ID for the entire flow
        request_id: Request ID for the current request
        session_id: Session ID for the user session
        user_id: User ID for the authenticated user
    """
    if correlation_id:
        correlation_id_var.set(correlation_id)
    if request_id:
        request_id_var.set(request_id)
    if session_id:
        session_id_var.set(session_id)
    if user_id:
        user_id_var.set(user_id)


def get_correlation_context() -> Dict[str, Optional[str]]:
    """Get current correlation context."""
    return {
        'correlation_id': correlation_id_var.get(),
        'request_id': request_id_var.get(),
        'session_id': session_id_var.get(),
        'user_id': user_id_var.get()
    }


# Decorators for automatic correlation tracking
def with_correlation(func):
    """
    Decorator that ensures correlation ID exists for the function execution.
    """
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if not correlation_id_var.get():
            correlation_id_var.set(generate_correlation_id())
        return func(*args, **kwargs)
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if not correlation_id_var.get():
            correlation_id_var.set(generate_correlation_id())
        return await func(*args, **kwargs)
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def log_execution_time(logger: StructuredLogger, operation: str):
    """
    Decorator that logs execution time of a function.
    
    Args:
        logger: StructuredLogger instance
        operation: Name of the operation
    """
    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.log_performance(operation, duration_ms, status='success')
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.log_performance(operation, duration_ms, status='error', error=str(e))
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.log_performance(operation, duration_ms, status='success')
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.log_performance(operation, duration_ms, status='error', error=str(e))
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# FastAPI Middleware for automatic correlation ID injection
class CorrelationMiddleware:
    """
    FastAPI middleware that automatically manages correlation IDs.
    """
    
    def __init__(self, app, logger: Optional[StructuredLogger] = None):
        self.app = app
        self.logger = logger or StructuredLogger(__name__)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract or generate correlation IDs
            headers = dict(scope.get("headers", []))
            
            correlation_id = headers.get(b"x-correlation-id", b"").decode() or generate_correlation_id()
            request_id = headers.get(b"x-request-id", b"").decode() or generate_request_id()
            
            # Set context
            correlation_id_var.set(correlation_id)
            request_id_var.set(request_id)
            
            # Log request start
            start_time = time.time()
            path = scope["path"]
            method = scope["method"]
            
            self.logger.info(
                f"Request started: {method} {path}",
                http_method=method,
                http_path=path,
                event_type='request_start'
            )
            
            # Process request
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    # Add correlation headers to response
                    headers = dict(message.get("headers", []))
                    headers[b"x-correlation-id"] = correlation_id.encode()
                    headers[b"x-request-id"] = request_id.encode()
                    message["headers"] = list(headers.items())
                    
                    # Log response
                    duration_ms = (time.time() - start_time) * 1000
                    status_code = message.get("status", 0)
                    
                    self.logger.log_api_request(
                        method=method,
                        path=path,
                        status_code=status_code,
                        duration_ms=duration_ms
                    )
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


# Global logger factory
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, level: str = "INFO") -> StructuredLogger:
    """
    Get or create a structured logger.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        
    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, level)
    return _loggers[name]


# Example usage and testing
if __name__ == "__main__":
    # Create logger
    logger = get_logger(__name__)
    
    # Set correlation context
    set_correlation_context(
        correlation_id=generate_correlation_id(),
        request_id=generate_request_id(),
        session_id="session_123",
        user_id="user_456"
    )
    
    # Log various events
    logger.info("Application started", version="2.1.0", environment="development")
    
    # Log with performance metrics
    logger.log_performance("database_query", 45.3, query_type="select", rows=150)
    
    # Log API request
    logger.log_api_request("POST", "/api/sessions", 201, 123.5, 
                          request_size=1024, response_size=256)
    
    # Log LLM call
    logger.log_llm_call("gemini-2.5-flash", "extract_codes", 500, 200, 1250.0,
                       confidence=0.95, codes_found=5)
    
    # Log exception
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.log_exception("Operation failed", e, operation="test_operation")
    
    # Test decorator
    @with_correlation
    @log_execution_time(logger, "test_function")
    async def test_async_function():
        await asyncio.sleep(0.1)
        logger.info("Inside async function")
        return "Success"
    
    # Run async test
    asyncio.run(test_async_function())
    
    print("\n✅ Structured logging system ready!")