#!/usr/bin/env python3
"""
Enhanced Configuration Manager

Supports complex, hierarchical configuration with behavioral validation.
Manages 15+ configuration categories with plugin integration.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)

class MethodologyType(Enum):
    """Research methodology paradigms"""
    GROUNDED_THEORY = "grounded_theory"
    THEMATIC_ANALYSIS = "thematic_analysis" 
    PHENOMENOLOGICAL = "phenomenological"
    CRITICAL_THEORY = "critical_theory"
    CONSTRUCTIVIST = "constructivist"
    FEMINIST = "feminist"
    POSTMODERN = "postmodern"
    EXPERT_QUALITATIVE = "expert_qualitative_coder"

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

@dataclass
class MethodologyConfig:
    """Research methodology configuration"""
    paradigm: MethodologyType
    theoretical_sensitivity: str  # low, medium, high
    coding_depth: str            # surface, focused, intensive
    memo_generation: bool = True
    saturation_criteria: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class ExtractionConfig:
    """Extraction behavior configuration"""
    coding_approach: CodingApproach
    extractor: str = "hierarchical"  # hierarchical, relationship, semantic, validated
    hierarchy_depth: int = 3
    relationship_threshold: float = 0.7
    minimum_frequency: int = 2
    entity_approach: str = "open"
    speaker_approach: str = "open"

@dataclass
class ValidationConfig:
    """Quality validation configuration"""
    validation_level: ValidationLevel
    inter_rater_enabled: bool = False
    consistency_threshold: float = 0.8
    quality_checks: List[str] = field(default_factory=list)
    consolidation_enabled: bool = True

@dataclass
class LLMConfig:
    """LLM behavior configuration"""
    provider: str = "gemini"
    model: str = "gemini-2.0-flash-exp"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    max_retries: int = 4
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    prompt_templates: Dict[str, str] = field(default_factory=dict)

@dataclass
class OutputConfig:
    """Output format configuration"""
    report_formats: List[str] = field(default_factory=lambda: ["markdown", "json"])
    include_audit_trail: bool = True
    include_quotes: bool = True
    export_neo4j: bool = True
    visualization_enabled: bool = False

@dataclass
class PerformanceConfig:
    """Performance tuning configuration"""
    max_concurrent_interviews: int = 1
    parallel_processing: bool = False
    batch_size: int = 10
    memory_limit_mb: Optional[int] = None
    timeout_minutes: Optional[int] = None

@dataclass
class DatabaseConfig:
    """Neo4j database configuration"""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "devpassword"
    schema_version: str = "v2"
    relationship_types: List[str] = field(default_factory=list)
    indexing_enabled: bool = True

@dataclass
class ComprehensiveConfig:
    """Complete system configuration"""
    methodology: MethodologyConfig
    extraction: ExtractionConfig
    validation: ValidationConfig  
    llm: LLMConfig
    output: OutputConfig
    performance: PerformanceConfig
    database: DatabaseConfig
    
    # Plugin-specific configurations
    plugin_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

class EnhancedConfigManager:
    """Manages complex configuration hierarchy"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/qc_comprehensive.yaml"
        self.config: Optional[ComprehensiveConfig] = None
    
    def load_config(self) -> ComprehensiveConfig:
        """Load and validate comprehensive configuration"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}, creating default")
                return self._create_default_config()
            
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
            
            # Build configuration objects
            methodology = MethodologyConfig(
                paradigm=MethodologyType(data.get('methodology', {}).get('paradigm', 'grounded_theory')),
                theoretical_sensitivity=data.get('methodology', {}).get('theoretical_sensitivity', 'medium'),
                coding_depth=data.get('methodology', {}).get('coding_depth', 'focused'),
                memo_generation=data.get('methodology', {}).get('memo_generation', True)
            )
            
            extraction = ExtractionConfig(
                coding_approach=CodingApproach(data.get('extraction', {}).get('coding_approach', 'open')),
                extractor=data.get('extraction', {}).get('extractor', 'hierarchical'),
                hierarchy_depth=data.get('extraction', {}).get('hierarchy_depth', 3),
                relationship_threshold=data.get('extraction', {}).get('relationship_threshold', 0.7)
            )
            
            validation = ValidationConfig(
                validation_level=ValidationLevel(data.get('validation', {}).get('validation_level', 'standard')),
                inter_rater_enabled=data.get('validation', {}).get('inter_rater_enabled', False),
                consistency_threshold=data.get('validation', {}).get('consistency_threshold', 0.8),
                quality_checks=data.get('validation', {}).get('quality_checks', []),
                consolidation_enabled=data.get('validation', {}).get('consolidation_enabled', True)
            )
            
            llm = LLMConfig(
                provider=data.get('llm', {}).get('provider', 'gemini'),
                model=data.get('llm', {}).get('model', 'gemini-2.0-flash-exp'),
                temperature=data.get('llm', {}).get('temperature', 0.1),
                max_retries=data.get('llm', {}).get('max_retries', 4)
            )
            
            output = OutputConfig(
                report_formats=data.get('output', {}).get('report_formats', ['markdown', 'json']),
                include_audit_trail=data.get('output', {}).get('include_audit_trail', True),
                include_quotes=data.get('output', {}).get('include_quotes', True),
                export_neo4j=data.get('output', {}).get('export_neo4j', True)
            )
            
            performance = PerformanceConfig(
                max_concurrent_interviews=data.get('performance', {}).get('max_concurrent_interviews', 1),
                parallel_processing=data.get('performance', {}).get('parallel_processing', False),
                batch_size=data.get('performance', {}).get('batch_size', 10)
            )
            
            database = DatabaseConfig(
                uri=data.get('database', {}).get('uri', 'bolt://localhost:7687'),
                user=data.get('database', {}).get('user', 'neo4j'),
                password=data.get('database', {}).get('password', 'devpassword'),
                schema_version=data.get('database', {}).get('schema_version', 'v2')
            )
            
            self.config = ComprehensiveConfig(
                methodology=methodology,
                extraction=extraction,
                validation=validation,
                llm=llm,
                output=output,
                performance=performance,
                database=database,
                plugin_configs=data.get('plugins', {})
            )
            
            logger.info(f"Loaded comprehensive configuration from {self.config_path}")
            return self.config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.info("Using default configuration")
            return self._create_default_config()
    
    def _create_default_config(self) -> ComprehensiveConfig:
        """Create default comprehensive configuration"""
        return ComprehensiveConfig(
            methodology=MethodologyConfig(
                paradigm=MethodologyType.GROUNDED_THEORY,
                theoretical_sensitivity="medium",
                coding_depth="focused"
            ),
            extraction=ExtractionConfig(
                coding_approach=CodingApproach.OPEN,
                extractor="hierarchical"
            ),
            validation=ValidationConfig(
                validation_level=ValidationLevel.STANDARD
            ),
            llm=LLMConfig(),
            output=OutputConfig(),
            performance=PerformanceConfig(),
            database=DatabaseConfig()
        )
    
    def save_config(self, config: ComprehensiveConfig, path: Optional[str] = None):
        """Save configuration to file"""
        save_path = path or self.config_path
        
        # Convert to dictionary for YAML serialization
        config_dict = self._config_to_dict(config)
        
        try:
            config_file = Path(save_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                yaml.safe_dump(config_dict, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def _config_to_dict(self, config: ComprehensiveConfig) -> Dict[str, Any]:
        """Convert configuration object to dictionary"""
        return {
            'methodology': {
                'paradigm': config.methodology.paradigm.value,
                'theoretical_sensitivity': config.methodology.theoretical_sensitivity,
                'coding_depth': config.methodology.coding_depth,
                'memo_generation': config.methodology.memo_generation,
                'saturation_criteria': config.methodology.saturation_criteria
            },
            'extraction': {
                'coding_approach': config.extraction.coding_approach.value,
                'extractor': config.extraction.extractor,
                'hierarchy_depth': config.extraction.hierarchy_depth,
                'relationship_threshold': config.extraction.relationship_threshold,
                'minimum_frequency': config.extraction.minimum_frequency,
                'entity_approach': config.extraction.entity_approach,
                'speaker_approach': config.extraction.speaker_approach
            },
            'validation': {
                'validation_level': config.validation.validation_level.value,
                'inter_rater_enabled': config.validation.inter_rater_enabled,
                'consistency_threshold': config.validation.consistency_threshold,
                'quality_checks': config.validation.quality_checks,
                'consolidation_enabled': config.validation.consolidation_enabled
            },
            'llm': {
                'provider': config.llm.provider,
                'model': config.llm.model,
                'temperature': config.llm.temperature,
                'max_tokens': config.llm.max_tokens,
                'max_retries': config.llm.max_retries,
                'retry_delay': config.llm.retry_delay,
                'circuit_breaker_threshold': config.llm.circuit_breaker_threshold,
                'prompt_templates': config.llm.prompt_templates
            },
            'output': {
                'report_formats': config.output.report_formats,
                'include_audit_trail': config.output.include_audit_trail,
                'include_quotes': config.output.include_quotes,
                'export_neo4j': config.output.export_neo4j,
                'visualization_enabled': config.output.visualization_enabled
            },
            'performance': {
                'max_concurrent_interviews': config.performance.max_concurrent_interviews,
                'parallel_processing': config.performance.parallel_processing,
                'batch_size': config.performance.batch_size,
                'memory_limit_mb': config.performance.memory_limit_mb,
                'timeout_minutes': config.performance.timeout_minutes
            },
            'database': {
                'uri': config.database.uri,
                'user': config.database.user,
                'password': config.database.password,
                'schema_version': config.database.schema_version,
                'relationship_types': config.database.relationship_types,
                'indexing_enabled': config.database.indexing_enabled
            },
            'plugins': config.plugin_configs
        }
    
    def get_behavior_changes(self, config_a: ComprehensiveConfig, 
                           config_b: ComprehensiveConfig) -> List[str]:
        """Identify behavioral changes between configurations"""
        changes = []
        
        if config_a.methodology.paradigm != config_b.methodology.paradigm:
            changes.append("paradigm_change_affects_prompts")
        
        if config_a.extraction.coding_approach != config_b.extraction.coding_approach:
            changes.append("coding_approach_affects_extraction_strategy")
        
        if config_a.extraction.extractor != config_b.extraction.extractor:
            changes.append("extractor_change_affects_algorithm")
            
        if config_a.validation.validation_level != config_b.validation.validation_level:
            changes.append("validation_level_affects_quality_pipeline")
        
        if config_a.performance.parallel_processing != config_b.performance.parallel_processing:
            changes.append("performance_settings_affect_processing")
        
        if config_a.llm.temperature != config_b.llm.temperature:
            changes.append("llm_temperature_affects_response_variability")
            
        return changes
    
    def validate_config(self, config: ComprehensiveConfig) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []
        
        # Validate extractor exists
        valid_extractors = ['hierarchical', 'relationship', 'semantic', 'validated']
        if config.extraction.extractor not in valid_extractors:
            issues.append(f"Invalid extractor: {config.extraction.extractor}")
        
        # Validate thresholds
        if not (0.0 <= config.extraction.relationship_threshold <= 1.0):
            issues.append("relationship_threshold must be between 0.0 and 1.0")
        
        if not (0.0 <= config.validation.consistency_threshold <= 1.0):
            issues.append("consistency_threshold must be between 0.0 and 1.0")
        
        if not (0.0 <= config.llm.temperature <= 2.0):
            issues.append("llm temperature must be between 0.0 and 2.0")
        
        # Validate performance settings
        if config.performance.max_concurrent_interviews < 1:
            issues.append("max_concurrent_interviews must be at least 1")
            
        return issues