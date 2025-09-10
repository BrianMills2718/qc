"""
Validation system for qualitative coding analysis.

This module provides intelligent validation, consolidation, and quality control
for extracted entities and relationships.
"""

from .entity_consolidator import EntityConsolidator, ConsolidationResult
from .relationship_consolidator import RelationshipConsolidator
from .quality_validator import QualityValidator, ValidationResult
from .validation_config import ValidationConfig, ValidationMode

__all__ = [
    'EntityConsolidator',
    'ConsolidationResult', 
    'RelationshipConsolidator',
    'QualityValidator',
    'ValidationResult',
    'ValidationConfig',
    'ValidationMode'
]