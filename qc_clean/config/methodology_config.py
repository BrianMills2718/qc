#!/usr/bin/env python3
"""
Methodology Configuration Management

Manages methodology-specific configurations for autonomous research workflows.
Provides configuration loading, validation, and management for grounded theory
and other qualitative research methodologies.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


@dataclass
class GroundedTheoryConfig:
    """Configuration for Grounded Theory analysis with LLM reliability settings"""
    methodology: str
    theoretical_sensitivity: str
    coding_depth: str
    memo_generation_frequency: str
    report_formats: List[str]
    include_audit_trail: bool
    include_supporting_quotes: bool
    minimum_code_frequency: int
    relationship_confidence_threshold: float
    validation_level: str
    temperature: float
    max_tokens: Optional[int]
    model_preference: str
    
    # LLM Reliability Settings
    max_llm_retries: int = 4
    base_retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: Optional[int] = None  # No timeout
    request_timeout: Optional[int] = None  # No timeout
    
    def __post_init__(self):
        """Validate configuration values after initialization"""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration parameters"""
        # Validate theoretical sensitivity
        valid_sensitivity = ["high", "medium", "low"]
        if self.theoretical_sensitivity not in valid_sensitivity:
            raise ValueError(f"theoretical_sensitivity must be one of {valid_sensitivity}")
        
        # Validate coding depth
        valid_depth = ["comprehensive", "focused", "minimal"]
        if self.coding_depth not in valid_depth:
            raise ValueError(f"coding_depth must be one of {valid_depth}")
        
        # Validate memo frequency
        valid_frequency = ["each_phase", "final_only", "none"]
        if self.memo_generation_frequency not in valid_frequency:
            raise ValueError(f"memo_generation_frequency must be one of {valid_frequency}")
        
        # Validate report formats
        valid_formats = ["academic_report", "executive_summary", "raw_data"]
        for fmt in self.report_formats:
            if fmt not in valid_formats:
                raise ValueError(f"report format '{fmt}' must be one of {valid_formats}")
        
        # Validate validation level
        valid_validation = ["standard", "rigorous", "minimal"]
        if self.validation_level not in valid_validation:
            raise ValueError(f"validation_level must be one of {valid_validation}")
        
        # Validate numeric ranges
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError("temperature must be between 0.0 and 1.0")
        
        if not 0.0 <= self.relationship_confidence_threshold <= 1.0:
            raise ValueError("relationship_confidence_threshold must be between 0.0 and 1.0")
        
        if self.minimum_code_frequency < 1:
            raise ValueError("minimum_code_frequency must be at least 1")
        
        # Validate retry parameters
        if self.max_llm_retries < 0 or self.max_llm_retries > 10:
            raise ValueError("max_llm_retries must be between 0 and 10")
        
        if self.base_retry_delay < 0.1 or self.base_retry_delay > 10.0:
            raise ValueError("base_retry_delay must be between 0.1 and 10.0 seconds")
        
        if self.circuit_breaker_threshold < 1 or self.circuit_breaker_threshold > 20:
            raise ValueError("circuit_breaker_threshold must be between 1 and 20")
        
        # Timeouts removed - no validation needed
        # if self.circuit_breaker_timeout and (self.circuit_breaker_timeout < 30 or self.circuit_breaker_timeout > 3600):
        #     raise ValueError("circuit_breaker_timeout must be between 30 and 3600 seconds")
        
        # if self.request_timeout and (self.request_timeout < 10 or self.request_timeout > 300):
        #     raise ValueError("request_timeout must be between 10 and 300 seconds")
        
        logger.info(f"Configuration validated: {self.methodology} with {self.coding_depth} depth, retries={self.max_llm_retries}")
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> 'GroundedTheoryConfig':
        """Load configuration from YAML file"""
        try:
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Check if this is a flat structure (new format) or nested structure (old format)
            is_flat_structure = 'theoretical_sensitivity' in config_data
            
            if is_flat_structure:
                # New flat structure (e.g., grounded_theory_reliable.yaml)
                return cls(
                    methodology=config_data.get('methodology', 'grounded_theory'),
                    theoretical_sensitivity=config_data.get('theoretical_sensitivity', 'high'),
                    coding_depth=config_data.get('coding_depth', 'comprehensive'),
                    memo_generation_frequency=config_data.get('memo_generation_frequency', 'each_phase'),
                    report_formats=config_data.get('report_formats', ['academic_report']),
                    include_audit_trail=config_data.get('include_audit_trail', True),
                    include_supporting_quotes=config_data.get('require_supporting_quotes', True),
                    minimum_code_frequency=config_data.get('minimum_code_frequency', 2),
                    relationship_confidence_threshold=config_data.get('relationship_confidence_threshold', 0.7),
                    validation_level=config_data.get('validation_level', 'standard'),
                    temperature=config_data.get('temperature', 0.0),
                    max_tokens=config_data.get('max_tokens'),
                    model_preference=config_data.get('model_preference', 'gemini/gemini-2.5-flash'),
                    # Retry parameters (with defaults for backward compatibility)
                    max_llm_retries=config_data.get('max_llm_retries', 4),
                    base_retry_delay=config_data.get('base_retry_delay', 1.0),
                    circuit_breaker_threshold=config_data.get('circuit_breaker_threshold', 5),
                    circuit_breaker_timeout=config_data.get('circuit_breaker_timeout', None),
                    request_timeout=config_data.get('request_timeout', None)
                )
            else:
                # Original nested structure (backward compatibility)
                analysis_params = config_data.get('analysis_parameters', {})
                output_config = config_data.get('output_configuration', {})
                quality_settings = config_data.get('quality_settings', {})
                llm_parameters = config_data.get('llm_parameters', {})
                
                return cls(
                    methodology=config_data.get('methodology', 'grounded_theory'),
                    theoretical_sensitivity=analysis_params.get('theoretical_sensitivity', 'high'),
                    coding_depth=analysis_params.get('coding_depth', 'comprehensive'),
                    memo_generation_frequency=analysis_params.get('memo_generation_frequency', 'each_phase'),
                    report_formats=output_config.get('report_formats', ['academic_report']),
                    include_audit_trail=output_config.get('include_audit_trail', True),
                    include_supporting_quotes=output_config.get('include_supporting_quotes', True),
                    minimum_code_frequency=quality_settings.get('minimum_code_frequency', 2),
                    relationship_confidence_threshold=quality_settings.get('relationship_confidence_threshold', 0.7),
                    validation_level=quality_settings.get('validation_level', 'standard'),
                    temperature=llm_parameters.get('temperature', 0.0),
                    max_tokens=llm_parameters.get('max_tokens'),
                    model_preference=llm_parameters.get('model_preference', 'gemini/gemini-2.5-flash'),
                    # Default retry parameters for backward compatibility
                    max_llm_retries=4,
                    base_retry_delay=1.0,
                    circuit_breaker_threshold=5,
                    circuit_breaker_timeout=None,
                    request_timeout=None
                )
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'methodology': self.methodology,
            'analysis_parameters': {
                'theoretical_sensitivity': self.theoretical_sensitivity,
                'coding_depth': self.coding_depth,
                'memo_generation_frequency': self.memo_generation_frequency
            },
            'output_configuration': {
                'report_formats': self.report_formats,
                'include_audit_trail': self.include_audit_trail,
                'include_supporting_quotes': self.include_supporting_quotes
            },
            'quality_settings': {
                'minimum_code_frequency': self.minimum_code_frequency,
                'relationship_confidence_threshold': self.relationship_confidence_threshold,
                'validation_level': self.validation_level
            },
            'llm_parameters': {
                'temperature': self.temperature,
                'max_tokens': self.max_tokens,
                'model_preference': self.model_preference
            }
        }


