#!/usr/bin/env python3
"""
AI Taxonomy Plugin Implementation

This plugin provides AI taxonomy enhancement functionality 
as an optional extension to the core GT workflow.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Add path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from plugins.base import TaxonomyPlugin, PluginStatus
from .taxonomy_engine import TaxonomyEngine

logger = logging.getLogger(__name__)


class AITaxonomyPlugin(TaxonomyPlugin):
    """AI Taxonomy Plugin Implementation"""
    
    def __init__(self):
        super().__init__()
        self.taxonomy_engine: Optional[TaxonomyEngine] = None
        self.taxonomy_data: Optional[Dict[str, Any]] = None
        self.taxonomy_file: Optional[str] = None
        self._logger = logging.getLogger(f"{__name__}.AITaxonomyPlugin")
    
    def get_name(self) -> str:
        """Return plugin name"""
        return "ai_taxonomy"
    
    def get_version(self) -> str:
        """Return plugin version"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return plugin description"""
        return "AI Taxonomy enhancement for GT codes and categories"
    
    def get_dependencies(self) -> List[str]:
        """Return plugin dependencies"""
        return ["core.workflow.grounded_theory"]
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize taxonomy plugin with configuration"""
        try:
            self._logger.info("Initializing AI Taxonomy plugin...")
            
            # Store configuration
            self._config = config
            
            # Extract taxonomy settings
            self.taxonomy_file = config.get('taxonomy_file', 'config/taxonomy/ai_taxonomy.yaml')
            auto_enhance = config.get('auto_enhance', False)
            enhancement_threshold = config.get('enhancement_threshold', 0.7)
            
            # Initialize taxonomy engine
            self.taxonomy_engine = TaxonomyEngine(
                auto_enhance=auto_enhance,
                threshold=enhancement_threshold
            )
            
            # Load taxonomy if file specified
            if self.taxonomy_file:
                if self.load_taxonomy(self.taxonomy_file):
                    self._logger.info(f"Loaded taxonomy from {self.taxonomy_file}")
                else:
                    self._logger.warning(f"Could not load taxonomy from {self.taxonomy_file}, using default")
                    self._load_default_taxonomy()
            else:
                self._load_default_taxonomy()
            
            self.status = PluginStatus.INITIALIZED
            self._logger.info("AI Taxonomy plugin initialized successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to initialize taxonomy plugin: {e}")
            self.status = PluginStatus.ERROR
            return False
    
    def is_available(self) -> bool:
        """Check if taxonomy plugin dependencies are available"""
        try:
            # Basic requirements are met with standard libraries
            return True
            
        except Exception as e:
            self._logger.error(f"Taxonomy plugin availability check failed: {e}")
            return False
    
    def load_taxonomy(self, taxonomy_path: str) -> bool:
        """Load AI taxonomy from file"""
        try:
            path = Path(taxonomy_path)
            
            # Check if path exists
            if not path.exists():
                self._logger.warning(f"Taxonomy file not found: {taxonomy_path}")
                return False
            
            # Load taxonomy data
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix == '.yaml' or path.suffix == '.yml':
                    self.taxonomy_data = yaml.safe_load(f)
                elif path.suffix == '.json':
                    import json
                    self.taxonomy_data = json.load(f)
                else:
                    self._logger.error(f"Unsupported taxonomy format: {path.suffix}")
                    return False
            
            # Pass taxonomy to engine
            if self.taxonomy_engine:
                self.taxonomy_engine.set_taxonomy(self.taxonomy_data)
            
            self._logger.info(f"Loaded taxonomy with {len(self.taxonomy_data.get('categories', []))} categories")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to load taxonomy from {taxonomy_path}: {e}")
            return False
    
    def _load_default_taxonomy(self) -> None:
        """Load default AI taxonomy"""
        self.taxonomy_data = {
            "name": "Default AI Taxonomy",
            "version": "1.0.0",
            "categories": [
                {
                    "id": "ai_capabilities",
                    "name": "AI Capabilities",
                    "subcategories": [
                        "natural_language_processing",
                        "computer_vision",
                        "machine_learning",
                        "deep_learning",
                        "reinforcement_learning"
                    ]
                },
                {
                    "id": "ai_applications",
                    "name": "AI Applications",
                    "subcategories": [
                        "automation",
                        "prediction",
                        "classification",
                        "generation",
                        "optimization"
                    ]
                },
                {
                    "id": "ai_ethics",
                    "name": "AI Ethics & Society",
                    "subcategories": [
                        "bias_fairness",
                        "transparency",
                        "accountability",
                        "privacy",
                        "safety"
                    ]
                },
                {
                    "id": "ai_limitations",
                    "name": "AI Limitations",
                    "subcategories": [
                        "data_dependency",
                        "interpretability",
                        "generalization",
                        "computational_cost",
                        "robustness"
                    ]
                },
                {
                    "id": "human_ai_interaction",
                    "name": "Human-AI Interaction",
                    "subcategories": [
                        "trust",
                        "collaboration",
                        "augmentation",
                        "control",
                        "understanding"
                    ]
                }
            ],
            "keywords": {
                "ai_capabilities": ["model", "algorithm", "training", "inference", "architecture"],
                "ai_applications": ["use case", "deployment", "implementation", "solution", "system"],
                "ai_ethics": ["ethical", "responsible", "fair", "transparent", "accountable"],
                "ai_limitations": ["challenge", "limitation", "constraint", "issue", "problem"],
                "human_ai_interaction": ["user", "human", "interaction", "interface", "experience"]
            }
        }
        
        if self.taxonomy_engine:
            self.taxonomy_engine.set_taxonomy(self.taxonomy_data)
        
        self._logger.info("Loaded default AI taxonomy")
    
    def enhance_codes(self, codes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance GT codes with taxonomy information"""
        if not self.taxonomy_engine:
            self._logger.error("Taxonomy engine not initialized")
            return codes
        
        try:
            self._logger.info(f"Enhancing {len(codes)} codes with taxonomy...")
            
            enhanced_codes = []
            for code in codes:
                enhanced_code = self.taxonomy_engine.enhance_code(code)
                enhanced_codes.append(enhanced_code)
            
            # Count enhancements
            enhanced_count = sum(1 for c in enhanced_codes if c.get('taxonomy_categories'))
            self._logger.info(f"Enhanced {enhanced_count}/{len(codes)} codes with taxonomy categories")
            
            return enhanced_codes
            
        except Exception as e:
            self._logger.error(f"Failed to enhance codes: {e}")
            return codes
    
    def suggest_categories(self, code_text: str) -> List[str]:
        """Suggest taxonomy categories for code"""
        if not self.taxonomy_engine:
            self._logger.error("Taxonomy engine not initialized")
            return []
        
        try:
            suggestions = self.taxonomy_engine.suggest_categories(code_text)
            
            if suggestions:
                self._logger.debug(f"Suggested {len(suggestions)} categories for '{code_text}'")
            
            return suggestions
            
        except Exception as e:
            self._logger.error(f"Failed to suggest categories for '{code_text}': {e}")
            return []
    
    def get_taxonomy_structure(self) -> Dict[str, Any]:
        """Get current taxonomy structure"""
        if not self.taxonomy_data:
            return {}
        
        return {
            "name": self.taxonomy_data.get("name", "Unknown"),
            "version": self.taxonomy_data.get("version", "Unknown"),
            "categories_count": len(self.taxonomy_data.get("categories", [])),
            "categories": [
                {
                    "id": cat.get("id"),
                    "name": cat.get("name"),
                    "subcategories_count": len(cat.get("subcategories", []))
                }
                for cat in self.taxonomy_data.get("categories", [])
            ]
        }
    
    def cleanup(self) -> bool:
        """Cleanup taxonomy plugin resources"""
        try:
            self._logger.info("Cleaning up taxonomy plugin resources...")
            
            # Clean up engine
            if self.taxonomy_engine:
                self.taxonomy_engine = None
            
            # Clear data
            self.taxonomy_data = None
            self.taxonomy_file = None
            
            self.status = PluginStatus.DISABLED
            self._logger.info("Taxonomy plugin cleanup completed")
            return True
            
        except Exception as e:
            self._logger.error(f"Error during taxonomy plugin cleanup: {e}")
            return False