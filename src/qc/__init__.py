"""
Bridge module for qc package
Provides compatibility layer between sophisticated system and current qc_clean infrastructure
"""

# Import key modules for bridge compatibility
from . import extraction
from . import core
from . import llm
from . import prompts

__all__ = ['extraction', 'core', 'llm', 'prompts']