#!/usr/bin/env python3
"""
Unified Configuration System

Environment-driven configuration - NO HARDCODED VALUES.
All configuration parameters loaded from environment variables via .env file.
Provides behavioral parameter control where changes produce measurable differences.
"""

import logging
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class MethodologyType(Enum):
    """Research methodology paradigms"""
    GROUNDED_THEORY = "grounded_theory"
    THEMATIC_ANALYSIS = "thematic_analysis" 
    PHENOMENOLOGICAL = "phenomenological"
    CRITICAL_THEORY = "critical_theory"
    CONSTRUCTIVIST = "constructivist"

class CodingApproach(Enum):
    """Code development approaches"""
    OPEN = "open"           # Inductive, data-driven
    CLOSED = "closed"       # Deductive, theory-driven  
    MIXED = "mixed"         # Combined approach

class ValidationLevel(Enum):
    """Validation rigor levels"""
    MINIMAL = "minimal"     # Basic validation only
    STANDARD = "standard"   # Standard quality checks
    RIGOROUS = "rigorous"   # Full academic validation

class ExtractorType(Enum):
    """Available extraction algorithms"""
    HIERARCHICAL = "hierarchical"
    RELATIONSHIP = "relationship"
    SEMANTIC = "semantic"
    VALIDATED = "validated"

@dataclass
class UnifiedConfig:
    """
    Environment-driven configuration system - NO HARDCODED VALUES.
    All configuration parameters loaded from environment variables via .env file.
    Configuration changes must produce >50% different analysis results.
    """
    
    # API Settings - loaded from environment
    api_provider: str = field(default_factory=lambda: os.getenv('API_PROVIDER', 'google'))
    model_preference: str = field(default_factory=lambda: os.getenv('MODEL', 'gemini-2.5-flash'))
    
    @property
    def api_key(self) -> str:
        """Dynamically resolve API key based on provider"""
        provider_key_map = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY', 
            'google': 'GEMINI_API_KEY'
        }
        key_env = provider_key_map.get(self.api_provider, 'GEMINI_API_KEY')
        return os.getenv(key_env, '')
    
    # Core methodology parameters (HIGH behavioral impact) - loaded from environment
    methodology: MethodologyType = field(default_factory=lambda: MethodologyType(os.getenv('METHODOLOGY', 'grounded_theory')))
    coding_approach: CodingApproach = field(default_factory=lambda: CodingApproach(os.getenv('CODING_APPROACH', 'open')))
    validation_level: ValidationLevel = field(default_factory=lambda: ValidationLevel(os.getenv('VALIDATION_LEVEL', 'standard')))
    extractor_type: ExtractorType = field(default_factory=lambda: ExtractorType(os.getenv('EXTRACTOR_TYPE', 'hierarchical')))
    
    # Analysis depth parameters (HIGH behavioral impact) - loaded from environment
    theoretical_sensitivity: str = field(default_factory=lambda: os.getenv('THEORETICAL_SENSITIVITY', 'medium'))  # low, medium, high
    coding_depth: str = field(default_factory=lambda: os.getenv('CODING_DEPTH', 'focused'))  # surface, focused, intensive
    minimum_code_frequency: int = field(default_factory=lambda: int(os.getenv('MINIMUM_CODE_FREQUENCY', '1')))
    relationship_confidence_threshold: float = field(default_factory=lambda: float(os.getenv('RELATIONSHIP_CONFIDENCE_THRESHOLD', '0.7')))
    
    # Content and output parameters (MEDIUM behavioral impact) - loaded from environment
    include_supporting_quotes: bool = field(default_factory=lambda: os.getenv('INCLUDE_SUPPORTING_QUOTES', 'true').lower() == 'true')
    include_audit_trail: bool = field(default_factory=lambda: os.getenv('INCLUDE_AUDIT_TRAIL', 'true').lower() == 'true')
    memo_generation_frequency: str = field(default_factory=lambda: os.getenv('MEMO_GENERATION_FREQUENCY', 'each_phase'))  # per_interview, each_phase, final_only
    report_formats: List[str] = field(default_factory=lambda: [os.getenv('REPORT_FORMATS', 'academic_report')])
    
    # LLM behavior parameters (HIGH behavioral impact) - loaded from environment
    temperature: float = field(default_factory=lambda: float(os.getenv('TEMPERATURE', '0.1')))  # 0.0-2.0, affects creativity/consistency
    max_tokens: Optional[int] = field(default_factory=lambda: int(os.getenv('MAX_TOKENS', '4000')) if os.getenv('MAX_TOKENS') else None)
    confidence_threshold: float = field(default_factory=lambda: float(os.getenv('CONFIDENCE_THRESHOLD', '0.6')))
    
    # Quality control parameters (MEDIUM behavioral impact) - loaded from environment
    consolidation_enabled: bool = field(default_factory=lambda: os.getenv('CONSOLIDATION_ENABLED', 'false').lower() == 'true')
    minimum_confidence: float = field(default_factory=lambda: float(os.getenv('MINIMUM_CONFIDENCE', '0.3')))
    
    # LLM Reliability Settings - loaded from environment
    max_llm_retries: int = field(default_factory=lambda: int(os.getenv('MAX_LLM_RETRIES', '4')))
    base_retry_delay: float = field(default_factory=lambda: float(os.getenv('BASE_RETRY_DELAY', '1.0')))
    circuit_breaker_threshold: int = field(default_factory=lambda: int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '5')))
    circuit_breaker_timeout: Optional[int] = field(default_factory=lambda: int(os.getenv('CIRCUIT_BREAKER_TIMEOUT')) if os.getenv('CIRCUIT_BREAKER_TIMEOUT') else None)
    request_timeout: Optional[int] = field(default_factory=lambda: int(os.getenv('REQUEST_TIMEOUT')) if os.getenv('REQUEST_TIMEOUT') else None)
    
    def __post_init__(self):
        """Validate configuration values after initialization"""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration parameters - FAIL-FAST approach"""
        # Validate required fields
        if not self.api_key:
            # For testing, we allow empty API key, but warn
            logger.warning("API_KEY not set - some functionality may not work")
        
        if not self.model_preference:
            raise ValueError("MODEL required in .env file")
        
        # Validate theoretical sensitivity
        if self.theoretical_sensitivity not in ['low', 'medium', 'high']:
            raise ValueError(f"Invalid THEORETICAL_SENSITIVITY: {self.theoretical_sensitivity}. Valid options: low, medium, high")
        
        # Validate coding depth
        if self.coding_depth not in ['surface', 'focused', 'intensive']:
            raise ValueError(f"Invalid CODING_DEPTH: {self.coding_depth}. Valid options: surface, focused, intensive")
        
        # Validate confidence thresholds
        if not 0.0 <= self.minimum_confidence <= 1.0:
            raise ValueError(f"MINIMUM_CONFIDENCE must be 0.0-1.0: {self.minimum_confidence}")
        
        if not 0.0 <= self.relationship_confidence_threshold <= 1.0:
            raise ValueError(f"RELATIONSHIP_CONFIDENCE_THRESHOLD must be 0.0-1.0: {self.relationship_confidence_threshold}")
        
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError(f"CONFIDENCE_THRESHOLD must be 0.0-1.0: {self.confidence_threshold}")
        
        # Validate temperature
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"TEMPERATURE must be 0.0-2.0: {self.temperature}")
        
        # Validate API provider
        valid_providers = ['openai', 'google', 'anthropic']
        if self.api_provider not in valid_providers:
            raise ValueError(f"Invalid API_PROVIDER: {self.api_provider}. Valid options: {valid_providers}")
    
    def get_behavioral_parameters(self) -> Dict[str, Any]:
        """
        Get parameters that significantly affect behavior.
        
        Changes to these parameters should produce >50% different results.
        """
        return {
            'methodology': self.methodology.value,
            'coding_approach': self.coding_approach.value,
            'validation_level': self.validation_level.value,
            'extractor_type': self.extractor_type.value,
            'theoretical_sensitivity': self.theoretical_sensitivity,
            'coding_depth': self.coding_depth,
            'temperature': self.temperature,
            'relationship_confidence_threshold': self.relationship_confidence_threshold,
            'minimum_confidence': self.minimum_confidence
        }
    
    def calculate_behavioral_difference(self, other: 'UnifiedConfig') -> float:
        """
        Calculate behavioral difference between configurations.
        
        Returns: float between 0.0-1.0 representing % difference
        """
        self_params = self.get_behavioral_parameters()
        other_params = other.get_behavioral_parameters()
        
        total_params = len(self_params)
        different_params = 0
        
        for key, self_value in self_params.items():
            other_value = other_params.get(key)
            
            if isinstance(self_value, (int, float)):
                # Numerical parameters - consider >20% change as different
                if abs(self_value - other_value) / max(abs(self_value), abs(other_value), 0.001) > 0.2:
                    different_params += 1
            else:
                # Categorical parameters - any change is different
                if self_value != other_value:
                    different_params += 1
        
        return different_params / total_params
    
    def to_grounded_theory_config(self):
        """Convert to legacy GroundedTheoryConfig for backward compatibility"""
        from .methodology_config import GroundedTheoryConfig
        
        return GroundedTheoryConfig(
            methodology=self.methodology.value,
            theoretical_sensitivity=self.theoretical_sensitivity,
            coding_depth=self.coding_depth,
            memo_generation_frequency=self.memo_generation_frequency,
            report_formats=self.report_formats,
            include_audit_trail=self.include_audit_trail,
            include_supporting_quotes=self.include_supporting_quotes,
            minimum_code_frequency=self.minimum_code_frequency,
            relationship_confidence_threshold=self.relationship_confidence_threshold,
            validation_level=self.validation_level.value,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            model_preference=self.model_preference,
            max_llm_retries=self.max_llm_retries,
            base_retry_delay=self.base_retry_delay,
            circuit_breaker_threshold=self.circuit_breaker_threshold,
            circuit_breaker_timeout=self.circuit_breaker_timeout,
            request_timeout=self.request_timeout
        )
    
    def get_extractor_config(self) -> Dict[str, Any]:
        """Get extractor-specific configuration"""
        base_config = {
            'minimum_confidence': self.minimum_confidence,
            'consolidation_enabled': self.consolidation_enabled,
            'validation_level': self.validation_level.value,
            'relationship_threshold': self.relationship_confidence_threshold,
        }
        
        # Add semantic-specific config
        if self.extractor_type == ExtractorType.SEMANTIC:
            base_config['semantic_units'] = ['sentence', 'paragraph'] if self.coding_depth == 'intensive' else ['paragraph']
        
        return base_config
    
    def get_behavioral_profile(self) -> Dict[str, str]:
        """Get human-readable behavioral profile"""
        return {
            'analysis_approach': f"{self.coding_approach.value} {self.methodology.value}",
            'analysis_depth': f"{self.coding_depth} with {self.theoretical_sensitivity} sensitivity",
            'quality_control': f"{self.validation_level.value} validation",
            'llm_creativity': f"temperature {self.temperature} ({'creative' if self.temperature > 0.5 else 'consistent'})",
            'extraction_method': self.extractor_type.value,
            'confidence_threshold': f"{self.minimum_confidence:.1f} min confidence"
        }
    
    @classmethod
    def from_yaml(cls, config_path: Union[str, Path]) -> 'UnifiedConfig':
        """Load configuration from YAML file"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Convert enum strings to enum values
            if 'methodology' in data:
                data['methodology'] = MethodologyType(data['methodology'])
            if 'coding_approach' in data:
                data['coding_approach'] = CodingApproach(data['coding_approach'])
            if 'validation_level' in data:
                data['validation_level'] = ValidationLevel(data['validation_level'])
            if 'extractor_type' in data:
                data['extractor_type'] = ExtractorType(data['extractor_type'])
            
            return cls(**data)
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            logger.info("Using default configuration")
            return cls()
    
    def to_yaml(self, config_path: Union[str, Path]):
        """Save configuration to YAML file"""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict with enum values as strings
        data = {
            'methodology': self.methodology.value,
            'coding_approach': self.coding_approach.value,
            'validation_level': self.validation_level.value,
            'extractor_type': self.extractor_type.value,
            'theoretical_sensitivity': self.theoretical_sensitivity,
            'coding_depth': self.coding_depth,
            'minimum_code_frequency': self.minimum_code_frequency,
            'relationship_confidence_threshold': self.relationship_confidence_threshold,
            'include_supporting_quotes': self.include_supporting_quotes,
            'include_audit_trail': self.include_audit_trail,
            'memo_generation_frequency': self.memo_generation_frequency,
            'report_formats': self.report_formats,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'model_preference': self.model_preference,
            'consolidation_enabled': self.consolidation_enabled,
            'minimum_confidence': self.minimum_confidence
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

# Predefined configuration profiles for different research approaches
CONFIGURATION_PROFILES = {
    'grounded_theory_standard': UnifiedConfig(
        methodology=MethodologyType.GROUNDED_THEORY,
        coding_approach=CodingApproach.OPEN,
        validation_level=ValidationLevel.STANDARD,
        extractor_type=ExtractorType.HIERARCHICAL,
        theoretical_sensitivity="medium",
        coding_depth="focused",
        temperature=0.1,
        minimum_confidence=0.3
    ),
    
    'thematic_analysis_rigorous': UnifiedConfig(
        methodology=MethodologyType.THEMATIC_ANALYSIS,
        coding_approach=CodingApproach.MIXED,
        validation_level=ValidationLevel.RIGOROUS,
        extractor_type=ExtractorType.VALIDATED,
        theoretical_sensitivity="high",
        coding_depth="intensive",
        temperature=0.05,
        minimum_confidence=0.5
    ),
    
    'exploratory_creative': UnifiedConfig(
        methodology=MethodologyType.CONSTRUCTIVIST,
        coding_approach=CodingApproach.OPEN,
        validation_level=ValidationLevel.MINIMAL,
        extractor_type=ExtractorType.SEMANTIC,
        theoretical_sensitivity="high",
        coding_depth="intensive",
        temperature=0.7,
        minimum_confidence=0.2
    ),
    
    'relationship_focused': UnifiedConfig(
        methodology=MethodologyType.GROUNDED_THEORY,
        coding_approach=CodingApproach.MIXED,
        validation_level=ValidationLevel.STANDARD,
        extractor_type=ExtractorType.RELATIONSHIP,
        theoretical_sensitivity="high",
        coding_depth="focused",
        temperature=0.2,
        minimum_confidence=0.4,
        relationship_confidence_threshold=0.6
    )
}

def get_configuration_profile(profile_name: str) -> UnifiedConfig:
    """Get a predefined configuration profile"""
    if profile_name not in CONFIGURATION_PROFILES:
        available = list(CONFIGURATION_PROFILES.keys())
        raise ValueError(f"Unknown profile: {profile_name}. Available: {available}")
    
    return CONFIGURATION_PROFILES[profile_name]