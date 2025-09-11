#!/usr/bin/env python3
"""
Extractor Plugin System

Registry and utility functions for extractor plugins.
"""

from typing import Dict, List, Optional, Any
from .base_extractor import ExtractorPlugin

_EXTRACTOR_REGISTRY: Dict[str, type] = {}

def register_extractor(name: str, extractor_class: type):
    """Register an extractor plugin"""
    if not issubclass(extractor_class, ExtractorPlugin):
        raise ValueError(f"Extractor {name} must inherit from ExtractorPlugin")
    _EXTRACTOR_REGISTRY[name] = extractor_class

def get_extractor_plugin(name: str) -> Optional[ExtractorPlugin]:
    """Get an extractor plugin by name"""
    if name not in _EXTRACTOR_REGISTRY:
        return None
    return _EXTRACTOR_REGISTRY[name]()

def get_available_extractors() -> List[str]:
    """Get list of available extractor names"""
    return list(_EXTRACTOR_REGISTRY.keys())

def list_extractor_capabilities() -> Dict[str, Dict[str, Any]]:
    """Get capabilities of all available extractors"""
    capabilities = {}
    for name, extractor_class in _EXTRACTOR_REGISTRY.items():
        extractor = extractor_class()
        capabilities[name] = extractor.get_capabilities()
    return capabilities

# Auto-register extractors when imported
def _auto_register_extractors():
    """Auto-register available extractor plugins"""
    try:
        from .hierarchical_extractor import HierarchicalExtractor
        register_extractor("hierarchical", HierarchicalExtractor)
    except ImportError:
        pass
        
    try:
        from .relationship_extractor import RelationshipExtractor
        register_extractor("relationship", RelationshipExtractor)
    except ImportError:
        pass
        
    try:
        from .semantic_extractor import SemanticExtractor
        register_extractor("semantic", SemanticExtractor)
    except ImportError:
        pass
        
    try:
        from .validated_extractor import ValidatedExtractor
        register_extractor("validated", ValidatedExtractor)
    except ImportError:
        pass
        
    try:
        from .enhanced_semantic_extractor import EnhancedSemanticExtractor
        register_extractor("enhanced_semantic", EnhancedSemanticExtractor)
    except ImportError:
        pass

# Register extractors on module import
_auto_register_extractors()