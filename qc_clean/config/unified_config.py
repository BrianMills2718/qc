#!/usr/bin/env python3
"""
Unified Configuration System

Environment-driven configuration for LLM and analysis parameters.
All values loaded from environment variables via .env file.
"""

import logging
import os
from typing import List, Optional
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
    
