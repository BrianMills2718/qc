"""
File Handler Utilities - File operations and validation for CLI
"""

import logging
import os
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = {'.txt', '.docx', '.doc', '.pdf', '.rtf'}
TEXT_EXTENSIONS = {'.txt'}
DOCUMENT_EXTENSIONS = {'.docx', '.doc', '.pdf', '.rtf'}


def discover_files(directory: str) -> List[str]:
    """
    Discover supported files in a directory
    
    Args:
        directory: Directory path to scan
        
    Returns:
        List of file paths found
        
    Raises:
        Exception: If directory doesn't exist or can't be accessed
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise Exception(f"Directory does not exist: {directory}")
    
    if not dir_path.is_dir():
        raise Exception(f"Path is not a directory: {directory}")
    
    discovered_files = []
    
    # Recursively search for supported files
    for file_path in dir_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            discovered_files.append(str(file_path))
    
    # Sort for consistent output
    discovered_files.sort()
    
    logger.info(f"Discovered {len(discovered_files)} files in {directory}")
    return discovered_files


def validate_file_formats(file_paths: List[str]) -> List[str]:
    """
    Validate file formats and accessibility
    
    Args:
        file_paths: List of file paths to validate
        
    Returns:
        List of validated file paths
        
    Raises:
        Exception: If validation fails
    """
    if not file_paths:
        raise Exception("No files provided for validation")
    
    validated_files = []
    errors = []
    
    for file_path in file_paths:
        path = Path(file_path)
        
        # Check existence
        if not path.exists():
            errors.append(f"File does not exist: {file_path}")
            continue
        
        # Check if it's a file
        if not path.is_file():
            errors.append(f"Path is not a file: {file_path}")
            continue
        
        # Check file extension
        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            errors.append(f"Unsupported file type '{extension}': {file_path}")
            continue
        
        # Check file size
        try:
            size = path.stat().st_size
            if size == 0:
                errors.append(f"File is empty: {file_path}")
                continue
            
            # Check for reasonable size limits (100MB max)
            if size > 100 * 1024 * 1024:
                errors.append(f"File too large (>100MB): {file_path}")
                continue
                
        except OSError as e:
            errors.append(f"Cannot access file {file_path}: {e}")
            continue
        
        # Check readability for text files
        if extension in TEXT_EXTENSIONS:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    # Try to read first few characters to validate encoding
                    f.read(100)
            except UnicodeDecodeError:
                try:
                    # Try with different encoding
                    with open(path, 'r', encoding='latin-1') as f:
                        f.read(100)
                    logger.warning(f"File {file_path} uses non-UTF-8 encoding")
                except Exception as e:
                    errors.append(f"Cannot read file {file_path}: {e}")
                    continue
            except Exception as e:
                errors.append(f"Cannot read file {file_path}: {e}")
                continue
        
        validated_files.append(file_path)
    
    if errors:
        error_msg = "File validation failed:\n" + "\n".join(errors)
        raise Exception(error_msg)
    
    if not validated_files:
        raise Exception("No valid files found after validation")
    
    logger.info(f"Validated {len(validated_files)} files successfully")
    return validated_files


def read_file_content(file_path: str) -> str:
    """
    Read the text content of a supported file.

    Handles .txt files directly and .docx/.pdf/.rtf via
    optional libraries (python-docx, PyPDF2, striprtf).
    Falls back to plain text reading for unsupported binary formats.

    Args:
        file_path: Path to the file

    Returns:
        The text content of the file

    Raises:
        Exception: If the file cannot be read
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == '.txt':
        for encoding in ('utf-8', 'latin-1'):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise Exception(f"Cannot decode text file: {file_path}")

    if ext in ('.docx', '.doc'):
        try:
            import docx
            doc = docx.Document(str(path))
            return '\n\n'.join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            logger.warning("python-docx not installed; falling back to raw text read")
            return path.read_text(errors='replace')

    if ext == '.pdf':
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(path))
            return '\n\n'.join(
                page.extract_text() or '' for page in reader.pages
            )
        except ImportError:
            logger.warning("PyPDF2 not installed; falling back to raw text read")
            return path.read_text(errors='replace')

    if ext == '.rtf':
        try:
            from striprtf.striprtf import rtf_to_text
            raw = path.read_bytes().decode('utf-8', errors='replace')
            return rtf_to_text(raw)
        except ImportError:
            logger.warning("striprtf not installed; falling back to raw text read")
            return path.read_text(errors='replace')

    # Fallback for any other extension
    return path.read_text(errors='replace')


def get_file_info(file_path: str) -> dict:
    """
    Get detailed information about a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    path = Path(file_path)
    
    if not path.exists():
        return {'error': 'File does not exist'}
    
    try:
        stat = path.stat()
        return {
            'name': path.name,
            'path': str(path.absolute()),
            'size': stat.st_size,
            'extension': path.suffix.lower(),
            'modified': stat.st_mtime,
            'readable': path.is_file() and os.access(path, os.R_OK)
        }
    except Exception as e:
        return {'error': str(e)}


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"