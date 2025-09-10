#!/usr/bin/env python3
"""
Base Extractor Plugin Interface

Defines the interface that all extraction plugins must implement.
Provides common functionality and ensures consistent plugin behavior.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum

class ExtractionPhase(Enum):
    """Extraction phases for multi-phase algorithms"""
    INITIAL = "initial" 
    RELATIONSHIP = "relationship"
    VALIDATION = "validation"
    FINALIZATION = "finalization"

class ExtractorPlugin(ABC):
    """Base interface for all extraction plugins"""
    
    def __init__(self):
        self.name = self.get_name()
        self.version = self.get_version()
        self.capabilities = self.get_capabilities()
    
    @abstractmethod
    def get_name(self) -> str:
        """Return unique extractor identifier"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Return extractor version"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return human-readable description"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return extractor capabilities and supported parameters"""
        pass
    
    @abstractmethod
    def extract_codes(self, interview_data: Dict[str, Any], 
                     config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract codes from interview data using this algorithm
        
        Args:
            interview_data: Interview content and metadata
            config: Algorithm-specific configuration
            
        Returns:
            List of extracted codes with metadata
        """
        pass
    
    @abstractmethod
    def supports_relationships(self) -> bool:
        """Return True if extractor can extract code relationships"""
        pass
    
    @abstractmethod
    def supports_hierarchy(self) -> bool:
        """Return True if extractor can create hierarchical codes"""
        pass
    
    @abstractmethod
    def get_required_config(self) -> List[str]:
        """Return list of required configuration parameters"""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration parameters"""
        required = self.get_required_config()
        return all(param in config for param in required)