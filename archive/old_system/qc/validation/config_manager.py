"""
Configuration management for validation system.

Supports loading and saving validation configurations from YAML files.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from .validation_config import ValidationConfig, ValidationMode, EntityMatchingMode, PropertyValidationMode

logger = logging.getLogger(__name__)


class ValidationConfigManager:
    """Manages loading and saving of validation configurations"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory to store configuration files (defaults to ~/.qc/validation)
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".qc" / "validation"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Validation config directory: {self.config_dir}")
    
    def save_config(self, config: ValidationConfig, name: str) -> Path:
        """
        Save validation configuration to YAML file
        
        Args:
            config: Validation configuration to save
            name: Name for the configuration file
            
        Returns:
            Path to saved configuration file
        """
        # Convert dataclass to dict
        config_dict = asdict(config)
        
        # Convert enums to strings for YAML serialization
        config_dict['entities'] = config.entities.value
        config_dict['relationships'] = config.relationships.value
        config_dict['entity_matching'] = config.entity_matching.value
        config_dict['property_validation'] = config.property_validation.value
        
        # Add metadata
        config_dict['_metadata'] = {
            'name': name,
            'created_by': 'ValidationConfigManager',
            'config_version': '1.0'
        }
        
        # Save to YAML file
        config_file = self.config_dir / f"{name}.yaml"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Saved validation config '{name}' to {config_file}")
        return config_file
    
    def load_config(self, name: str) -> ValidationConfig:
        """
        Load validation configuration from YAML file
        
        Args:
            name: Name of the configuration to load
            
        Returns:
            ValidationConfig object
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration file is invalid
        """
        config_file = self.config_dir / f"{name}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration '{name}' not found at {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            
            # Remove metadata
            config_dict.pop('_metadata', None)
            
            # Convert string values back to enums
            if 'entities' in config_dict:
                config_dict['entities'] = ValidationMode(config_dict['entities'])
            if 'relationships' in config_dict:
                config_dict['relationships'] = ValidationMode(config_dict['relationships'])
            if 'entity_matching' in config_dict:
                config_dict['entity_matching'] = EntityMatchingMode(config_dict['entity_matching'])
            if 'property_validation' in config_dict:
                config_dict['property_validation'] = PropertyValidationMode(config_dict['property_validation'])
            
            # Create ValidationConfig object
            config = ValidationConfig(**config_dict)
            
            logger.info(f"Loaded validation config '{name}' from {config_file}")
            return config
            
        except Exception as e:
            raise ValueError(f"Invalid configuration file '{name}': {e}") from e
    
    def list_configs(self) -> List[str]:
        """
        List all available configuration names
        
        Returns:
            List of configuration names (without .yaml extension)
        """
        config_files = list(self.config_dir.glob("*.yaml"))
        return [f.stem for f in config_files]
    
    def delete_config(self, name: str) -> bool:
        """
        Delete a validation configuration
        
        Args:
            name: Name of configuration to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        config_file = self.config_dir / f"{name}.yaml"
        
        if config_file.exists():
            config_file.unlink()
            logger.info(f"Deleted validation config '{name}'")
            return True
        else:
            logger.warning(f"Configuration '{name}' not found")
            return False
    
    def create_default_configs(self):
        """Create default validation configurations"""
        default_configs = {
            'academic_research': ValidationConfig.academic_research_config(),
            'exploratory_research': ValidationConfig.exploratory_research_config(),
            'production_research': ValidationConfig.production_research_config(),
            'hybrid_default': ValidationConfig()
        }
        
        for name, config in default_configs.items():
            if not (self.config_dir / f"{name}.yaml").exists():
                self.save_config(config, name)
                logger.info(f"Created default config: {name}")
    
    def get_config_info(self, name: str) -> Dict[str, Any]:
        """
        Get information about a configuration without loading it
        
        Args:
            name: Configuration name
            
        Returns:
            Dictionary with configuration metadata and summary
        """
        config_file = self.config_dir / f"{name}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration '{name}' not found")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            
            metadata = config_dict.get('_metadata', {})
            
            return {
                'name': name,
                'file_path': str(config_file),
                'entities_mode': config_dict.get('entities', 'unknown'),
                'relationships_mode': config_dict.get('relationships', 'unknown'),
                'entity_matching': config_dict.get('entity_matching', 'unknown'),
                'consolidation_threshold': config_dict.get('consolidation_threshold', 'unknown'),
                'quality_threshold': config_dict.get('quality_threshold', 'unknown'),
                'auto_merge_similar': config_dict.get('auto_merge_similar', 'unknown'),
                'metadata': metadata
            }
            
        except Exception as e:
            return {
                'name': name,
                'file_path': str(config_file),
                'error': str(e)
            }
    
    def validate_config_file(self, name: str) -> Dict[str, Any]:
        """
        Validate a configuration file for correctness
        
        Args:
            name: Configuration name to validate
            
        Returns:
            Validation result with issues and warnings
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            config = self.load_config(name)
            
            # Validation checks
            if config.consolidation_threshold < 0 or config.consolidation_threshold > 1:
                result['errors'].append("consolidation_threshold must be between 0 and 1")
                result['valid'] = False
            
            if config.quality_threshold < 0 or config.quality_threshold > 1:
                result['errors'].append("quality_threshold must be between 0 and 1")
                result['valid'] = False
            
            if config.confidence_auto_approve <= config.confidence_flag_review:
                result['warnings'].append("auto_approve threshold should be higher than flag_review threshold")
            
            if config.confidence_flag_review <= config.confidence_require_validation:
                result['warnings'].append("flag_review threshold should be higher than require_validation threshold")
            
            # Configuration suggestions
            if config.entities == ValidationMode.CLOSED and not config.standard_entity_types:
                result['suggestions'].append("Consider defining standard_entity_types for closed mode")
            
            if config.relationships == ValidationMode.CLOSED and not config.standard_relationship_types:
                result['suggestions'].append("Consider defining standard_relationship_types for closed mode")
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Failed to load configuration: {e}")
        
        return result


def create_example_config() -> str:
    """
    Create an example configuration file content
    
    Returns:
        YAML string with example configuration
    """
    example_config = {
        '_metadata': {
            'name': 'example_config',
            'description': 'Example validation configuration with all options',
            'created_by': 'user',
            'config_version': '1.0'
        },
        'entities': 'hybrid',
        'relationships': 'hybrid',
        'entity_matching': 'smart',
        'property_validation': 'hybrid',
        'consolidation_threshold': 0.85,
        'auto_reject_unknown': False,
        'auto_merge_similar': True,
        'require_evidence': True,
        'quality_threshold': 0.7,
        'confidence_auto_approve': 0.9,
        'confidence_flag_review': 0.7,
        'confidence_require_validation': 0.5,
        'standard_entity_types': [
            'Person', 'Organization', 'Tool', 'Method', 'Concept'
        ],
        'standard_relationship_types': [
            'WORKS_AT', 'USES', 'MANAGES', 'PART_OF', 'IMPLEMENTS',
            'COLLABORATES_WITH', 'ADVOCATES_FOR', 'SKEPTICAL_OF'
        ]
    }
    
    return yaml.dump(example_config, default_flow_style=False, sort_keys=False)