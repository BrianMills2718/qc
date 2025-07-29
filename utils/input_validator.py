#!/usr/bin/env python3
"""
Comprehensive Input Validation and Sanitization System
Protects against injection attacks, validates data types, and sanitizes content
"""

import re
import html
import bleach
import unicodedata
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


class SecurityError(Exception):
    """Raised when security validation fails"""
    pass


class InputSanitizer:
    """Comprehensive input sanitization utilities"""
    
    # Dangerous patterns that indicate potential injection attacks
    INJECTION_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',               # XSS
        r'on\w+\s*=',                # Event handlers
        r'eval\s*\(',                # Code execution
        r'exec\s*\(',                # Code execution
        r'import\s+',                # Python imports
        r'__\w+__',                  # Python dunder methods
        r'\.\./',                    # Path traversal
        r'union\s+select',           # SQL injection
        r'drop\s+table',             # SQL injection
        r'delete\s+from',            # SQL injection
        r'insert\s+into',            # SQL injection
        r'update\s+.*\s+set',        # SQL injection
        r'/\*.*?\*/',                # SQL comments
        r'--\s',                     # SQL comments
        r';\s*drop',                 # SQL injection
        r';\s*delete',               # SQL injection
    ]
    
    # Allowed HTML tags for rich text content (very restrictive)
    ALLOWED_HTML_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
    ALLOWED_HTML_ATTRS = {}
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: Optional[int] = None, 
                       allow_html: bool = False) -> str:
        """
        Sanitize string input against various injection attacks.
        
        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow safe HTML tags
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If input fails validation
            SecurityError: If malicious content detected
        """
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value)}")
        
        # Check for null bytes and control characters
        if '\x00' in value:
            raise SecurityError("Null bytes not allowed in input")
        
        # Remove or escape control characters (except newlines and tabs)
        value = ''.join(char for char in value 
                       if ord(char) >= 32 or char in '\n\r\t')
        
        # Normalize unicode characters
        value = unicodedata.normalize('NFKC', value)
        
        # Check for injection patterns
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential injection attack detected: {pattern}")
                raise SecurityError(f"Suspicious pattern detected in input")
        
        # Handle HTML content
        if allow_html:
            # Use bleach to sanitize HTML
            value = bleach.clean(
                value, 
                tags=cls.ALLOWED_HTML_TAGS,
                attributes=cls.ALLOWED_HTML_ATTRS,
                strip=True
            )
        else:
            # Escape HTML entities
            value = html.escape(value)
        
        # Trim whitespace
        value = value.strip()
        
        # Check length
        if max_length and len(value) > max_length:
            raise ValidationError(f"Input too long: {len(value)} > {max_length}")
        
        return value
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
            
        Raises:
            ValidationError: If filename is invalid
        """
        if not isinstance(filename, str):
            raise ValidationError(f"Expected string filename, got {type(filename)}")
        
        # Remove directory separators and dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*', '\x00']
        for char in dangerous_chars:
            if char in filename:
                raise SecurityError(f"Dangerous character '{char}' in filename")
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + \
                        [f'COM{i}' for i in range(1, 10)] + \
                        [f'LPT{i}' for i in range(1, 10)]
        
        if filename.upper() in reserved_names:
            raise ValidationError(f"Reserved filename: {filename}")
        
        # Ensure reasonable length
        if len(filename) > 255:
            raise ValidationError(f"Filename too long: {len(filename)} > 255")
        
        if len(filename) == 0:
            raise ValidationError("Filename cannot be empty")
        
        return filename
    
    @classmethod
    def validate_uuid(cls, value: str) -> str:
        """
        Validate UUID format.
        
        Args:
            value: UUID string to validate
            
        Returns:
            Validated UUID string
            
        Raises:
            ValidationError: If UUID is invalid
        """
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, value, re.IGNORECASE):
            raise ValidationError(f"Invalid UUID format: {value}")
        return value.lower()
    
    @classmethod
    def validate_session_name(cls, name: str) -> str:
        """Validate session name with specific business rules"""
        name = cls.sanitize_string(name, max_length=100, allow_html=False)
        
        if len(name) < 1:
            raise ValidationError("Session name cannot be empty")
        
        # Only allow alphanumeric, spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
            raise ValidationError("Session name contains invalid characters")
        
        return name
    
    @classmethod
    def validate_memo_content(cls, content: str) -> str:
        """Validate memo content (allows basic HTML)"""
        content = cls.sanitize_string(content, max_length=10000, allow_html=True)
        
        if len(content.strip()) < 1:
            raise ValidationError("Memo content cannot be empty")
        
        return content


class ValidatedSessionCreate(BaseModel):
    """Validated session creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        return InputSanitizer.validate_session_name(v)


class ValidatedMemoCreate(BaseModel):
    """Validated memo creation request"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        return InputSanitizer.sanitize_string(v, max_length=200, allow_html=False)
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        return InputSanitizer.validate_memo_content(v)


class FileUploadValidator:
    """Validate file uploads"""
    
    ALLOWED_EXTENSIONS = {'.txt', '.docx'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def validate_upload(cls, filename: str, content: bytes) -> tuple[str, bytes]:
        """
        Validate uploaded file.
        
        Args:
            filename: Original filename
            content: File content bytes
            
        Returns:
            Tuple of (sanitized_filename, content)
            
        Raises:
            ValidationError: If file validation fails
        """
        # Sanitize filename
        safe_filename = InputSanitizer.sanitize_filename(filename)
        
        # Check file extension
        file_ext = '.' + safe_filename.split('.')[-1].lower() if '.' in safe_filename else ''
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            raise ValidationError(f"File type not allowed: {file_ext}")
        
        # Check file size
        if len(content) > cls.MAX_FILE_SIZE:
            raise ValidationError(f"File too large: {len(content)} > {cls.MAX_FILE_SIZE}")
        
        if len(content) == 0:
            raise ValidationError("File cannot be empty")
        
        # Basic content validation for text files
        if file_ext == '.txt':
            try:
                # Try to decode as UTF-8
                text_content = content.decode('utf-8')
                # Check for suspicious content
                InputSanitizer.sanitize_string(text_content, max_length=cls.MAX_FILE_SIZE)
            except UnicodeDecodeError:
                raise ValidationError("Text file must be valid UTF-8")
        
        return safe_filename, content


class ParameterValidator:
    """Validate URL and query parameters"""
    
    @classmethod
    def validate_session_id(cls, session_id: str) -> str:
        """Validate session ID parameter"""
        if not session_id or not isinstance(session_id, str):
            raise ValidationError("Session ID is required")
        
        return InputSanitizer.validate_uuid(session_id)
    
    @classmethod
    def validate_task_id(cls, task_id: str) -> str:
        """Validate task ID parameter"""
        if not task_id or not isinstance(task_id, str):
            raise ValidationError("Task ID is required")
        
        return InputSanitizer.validate_uuid(task_id)
    
    @classmethod
    def validate_code_id(cls, code_id: str) -> str:
        """Validate code ID parameter"""
        if not code_id or not isinstance(code_id, str):
            raise ValidationError("Code ID is required")
        
        return InputSanitizer.validate_uuid(code_id)
    
    @classmethod
    def validate_export_format(cls, format_param: str) -> str:
        """Validate export format parameter"""
        allowed_formats = {'csv', 'json'}
        
        if not format_param or not isinstance(format_param, str):
            return 'csv'  # Default format
        
        format_param = format_param.lower().strip()
        
        if format_param not in allowed_formats:
            raise ValidationError(f"Invalid export format: {format_param}")
        
        return format_param


# Convenience functions for common validations
def validate_and_sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Quick string validation and sanitization"""
    return InputSanitizer.sanitize_string(value, max_length=max_length, allow_html=False)


def validate_uuid_param(value: str) -> str:
    """Quick UUID validation"""
    return InputSanitizer.validate_uuid(value)


def validate_filename_param(value: str) -> str:
    """Quick filename validation"""
    return InputSanitizer.sanitize_filename(value)


# Test the validation system
if __name__ == "__main__":
    # Test basic sanitization
    try:
        safe_text = InputSanitizer.sanitize_string("Hello <script>alert('xss')</script> World")
        print(f"✅ Sanitized: {safe_text}")
        
        safe_filename = InputSanitizer.sanitize_filename("../../../etc/passwd")
        print(f"❌ This should fail")
    except SecurityError as e:
        print(f"✅ Security error caught: {e}")
    except ValidationError as e:
        print(f"✅ Validation error caught: {e}")
    
    # Test UUID validation
    try:
        uuid_val = InputSanitizer.validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        print(f"✅ Valid UUID: {uuid_val}")
    except ValidationError as e:
        print(f"❌ UUID validation failed: {e}")
    
    print("🔒 Input validation system ready!")