"""
Bridge import for LLM Handler
Redirects to current qc_clean infrastructure
"""

import sys
from pathlib import Path

# Add the project root to the path for qc_clean imports
# Go up from src/qc/llm/ to project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Bridge import to current system
from qc_clean.core.llm.llm_handler import LLMHandler
from qc_clean.core.llm.llm_handler import LLMHandler as BaseLLMHandler

# Export for compatibility
__all__ = ['LLMHandler', 'BaseLLMHandler']