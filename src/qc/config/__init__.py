"""
Configuration bridge module
"""

from .config_adapter import (
    create_extraction_config_from_unified,
    create_default_extraction_config,
    map_coding_approach
)

__all__ = [
    'create_extraction_config_from_unified',
    'create_default_extraction_config',
    'map_coding_approach'
]