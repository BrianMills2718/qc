#!/usr/bin/env python3
"""
QC Clean Plugin System - Base Plugin Interfaces

This module defines the core plugin interfaces for the QC Clean architecture.
All plugins must inherit from QCPlugin and implement the required methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """Plugin status enumeration"""
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class QCPlugin(ABC):
    """Base class for all QC system plugins"""
    
    def __init__(self):
        self.status = PluginStatus.UNINITIALIZED
        self._config = {}
        self._dependencies = []
        self._logger = logging.getLogger(f"{__name__}.{self.get_name()}")
    
    @abstractmethod
    def get_name(self) -> str:
        """Return plugin name for registry"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Return plugin version"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return plugin description"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Return list of required plugin dependencies"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if plugin dependencies are available"""
        pass
    
    def get_status(self) -> PluginStatus:
        """Get current plugin status"""
        return self.status
    
    def get_config(self) -> Dict[str, Any]:
        """Get plugin configuration"""
        return self._config.copy()
    
    def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        try:
            self.status = PluginStatus.DISABLED
            return True
        except Exception as e:
            self._logger.error(f"Error during cleanup: {e}")
            self.status = PluginStatus.ERROR
            return False


class QCAPlugin(QCPlugin):
    """QCA Analysis Plugin Interface"""
    
    @abstractmethod
    def can_process(self, gt_results: Dict[str, Any]) -> bool:
        """Check if GT results can be converted to QCA"""
        pass
    
    @abstractmethod
    def convert_to_qca(self, gt_results: Dict[str, Any]) -> Dict[str, Any]:
        """Convert GT codes to QCA conditions/outcomes"""
        pass
    
    @abstractmethod
    def run_qca_analysis(self, qca_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute QCA analysis pipeline"""
        pass
    
    def get_dependencies(self) -> List[str]:
        """QCA plugin dependencies"""
        return ["core.workflow.grounded_theory"]


class APIPlugin(QCPlugin):
    """Background API Plugin Interface"""
    
    @abstractmethod
    def start_server(self, host: str = "localhost", port: int = 8000) -> bool:
        """Start API server"""
        pass
    
    @abstractmethod
    def stop_server(self) -> bool:
        """Stop API server"""
        pass
    
    @abstractmethod
    def register_gt_endpoints(self, gt_workflow) -> None:
        """Register GT analysis endpoints"""
        pass
    
    @abstractmethod
    def enable_background_processing(self) -> bool:
        """Enable background task processing"""
        pass
    
    def get_dependencies(self) -> List[str]:
        """API plugin dependencies"""
        return ["core.cli.robust_cli_operations"]


class TaxonomyPlugin(QCPlugin):
    """AI Taxonomy Plugin Interface"""
    
    @abstractmethod
    def load_taxonomy(self, taxonomy_path: str) -> bool:
        """Load AI taxonomy from file"""
        pass
    
    @abstractmethod
    def enhance_codes(self, codes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance GT codes with taxonomy information"""
        pass
    
    @abstractmethod
    def suggest_categories(self, code_text: str) -> List[str]:
        """Suggest taxonomy categories for code"""
        pass
    
    def get_dependencies(self) -> List[str]:
        """Taxonomy plugin dependencies"""
        return ["core.workflow.grounded_theory"]


class PluginInterface:
    """Plugin interface definitions for type checking"""
    
    # Core interfaces that all plugins must implement
    CORE_METHODS = [
        "get_name", "get_version", "get_description", 
        "get_dependencies", "initialize", "is_available"
    ]
    
    # Specialized interface method groups
    QCA_METHODS = ["can_process", "convert_to_qca", "run_qca_analysis"]
    API_METHODS = ["start_server", "stop_server", "register_gt_endpoints", "enable_background_processing"]
    TAXONOMY_METHODS = ["load_taxonomy", "enhance_codes", "suggest_categories"]
    
    @staticmethod
    def validate_plugin_interface(plugin_instance: QCPlugin, expected_type: str = "core") -> List[str]:
        """Validate that plugin implements required interface methods"""
        missing_methods = []
        
        # Check core methods
        for method in PluginInterface.CORE_METHODS:
            if not hasattr(plugin_instance, method) or not callable(getattr(plugin_instance, method)):
                missing_methods.append(method)
        
        # Check specialized methods based on plugin type
        if expected_type == "qca" and isinstance(plugin_instance, QCAPlugin):
            for method in PluginInterface.QCA_METHODS:
                if not hasattr(plugin_instance, method) or not callable(getattr(plugin_instance, method)):
                    missing_methods.append(method)
        
        elif expected_type == "api" and isinstance(plugin_instance, APIPlugin):
            for method in PluginInterface.API_METHODS:
                if not hasattr(plugin_instance, method) or not callable(getattr(plugin_instance, method)):
                    missing_methods.append(method)
        
        elif expected_type == "taxonomy" and isinstance(plugin_instance, TaxonomyPlugin):
            for method in PluginInterface.TAXONOMY_METHODS:
                if not hasattr(plugin_instance, method) or not callable(getattr(plugin_instance, method)):
                    missing_methods.append(method)
        
        return missing_methods