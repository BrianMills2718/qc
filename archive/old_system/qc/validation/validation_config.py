"""
Configuration system for validation modes and thresholds.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


class ValidationMode(Enum):
    """Validation mode configuration"""
    CLOSED = "closed"      # Only standard entity/relationship types allowed
    OPEN = "open"          # Maximum LLM discovery flexibility
    HYBRID = "hybrid"      # Balanced approach using standard + discovered


class EntityMatchingMode(Enum):
    """Entity matching strategy for deduplication"""
    STRICT = "strict"      # Exact name matching
    FUZZY = "fuzzy"        # Similarity-based matching (>0.8)
    SMART = "smart"        # Try standard first, then fuzzy


class PropertyValidationMode(Enum):
    """Property validation strategy"""
    STRICT = "strict"      # Only standard properties allowed
    LOOSE = "loose"        # Allow any properties
    HYBRID = "hybrid"      # Standard properties + discovered


@dataclass
class ValidationConfig:
    """Configuration for validation system behavior"""
    
    # Core validation modes
    entities: ValidationMode = ValidationMode.HYBRID
    relationships: ValidationMode = ValidationMode.HYBRID
    
    # Matching and consolidation
    entity_matching: EntityMatchingMode = EntityMatchingMode.SMART
    property_validation: PropertyValidationMode = PropertyValidationMode.HYBRID
    consolidation_threshold: float = 0.85
    
    # Auto-processing behavior
    auto_reject_unknown: bool = False
    auto_merge_similar: bool = True
    require_evidence: bool = True
    
    # Quality thresholds
    quality_threshold: float = 0.7
    confidence_auto_approve: float = 0.9
    confidence_flag_review: float = 0.7
    confidence_require_validation: float = 0.5
    
    # Standard entity/relationship types (for closed/hybrid modes)
    standard_entity_types: List[str] = None
    standard_relationship_types: List[str] = None
    
    def __post_init__(self):
        """Set default standard types if not provided"""
        if self.standard_entity_types is None:
            self.standard_entity_types = [
                "Person", "Organization", "Tool", "Method", "Concept"
            ]
        
        if self.standard_relationship_types is None:
            self.standard_relationship_types = [
                "WORKS_AT", "USES", "MANAGES", "PART_OF", "IMPLEMENTS",
                "COLLABORATES_WITH", "ADVOCATES_FOR", "SKEPTICAL_OF"
            ]
    
    @classmethod
    def academic_research_config(cls) -> 'ValidationConfig':
        """Configuration for formal academic research requiring consistency"""
        return cls(
            entities=ValidationMode.CLOSED,
            relationships=ValidationMode.CLOSED,
            entity_matching=EntityMatchingMode.STRICT,
            property_validation=PropertyValidationMode.STRICT,
            quality_threshold=0.8,
            require_evidence=True,
            auto_reject_unknown=True
        )
    
    @classmethod
    def exploratory_research_config(cls) -> 'ValidationConfig':
        """Configuration for exploratory interviews discovering new patterns"""
        return cls(
            entities=ValidationMode.OPEN,
            relationships=ValidationMode.OPEN,
            entity_matching=EntityMatchingMode.FUZZY,
            property_validation=PropertyValidationMode.LOOSE,
            consolidation_threshold=0.75,
            quality_threshold=0.6,
            require_evidence=False,
            auto_merge_similar=True
        )
    
    @classmethod
    def production_research_config(cls) -> 'ValidationConfig':
        """Configuration for ongoing research with established framework"""
        return cls(
            entities=ValidationMode.HYBRID,
            relationships=ValidationMode.HYBRID,
            entity_matching=EntityMatchingMode.SMART,
            property_validation=PropertyValidationMode.HYBRID,
            consolidation_threshold=0.85,
            quality_threshold=0.7,
            auto_merge_similar=True,
            require_evidence=True
        )