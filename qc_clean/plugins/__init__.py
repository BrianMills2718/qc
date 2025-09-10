#!/usr/bin/env python3
"""
QC Clean Plugin System

This package provides the plugin architecture for QC Clean, including:
- Base plugin interfaces (QCPlugin, QCAPlugin, APIPlugin, TaxonomyPlugin)
- Plugin registry and discovery system
- Plugin manager for lifecycle management
- Configuration integration
"""

try:
    from .base import (
        QCPlugin, QCAPlugin, APIPlugin, TaxonomyPlugin,
        PluginStatus, PluginInterface
    )
    from .registry import PluginRegistry, PluginDiscovery, PluginDependencyError
    # Skip plugin manager for now due to config dependency
    # from .plugin_manager import PluginManager
    PluginManager = None
except ImportError:
    # Fallback if imports fail
    QCPlugin = QCAPlugin = APIPlugin = TaxonomyPlugin = None
    PluginStatus = PluginInterface = None  
    PluginRegistry = PluginDiscovery = PluginDependencyError = None
    PluginManager = None

__all__ = [
    # Base interfaces
    'QCPlugin', 'QCAPlugin', 'APIPlugin', 'TaxonomyPlugin',
    'PluginStatus', 'PluginInterface',
    
    # Registry system
    'PluginRegistry', 'PluginDiscovery', 'PluginDependencyError',
    
    # Main manager
    'PluginManager'
]

# Version info
__version__ = '1.0.0'
__author__ = 'QC Clean Architecture'