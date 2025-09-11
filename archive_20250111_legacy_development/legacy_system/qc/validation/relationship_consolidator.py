"""
Relationship consolidation logic for grouping semantically similar relationship types.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from difflib import SequenceMatcher

from ..extraction.extraction_schemas import ExtractedRelationship

logger = logging.getLogger(__name__)


class RelationshipConsolidator:
    """Consolidates semantically similar relationship types"""
    
    def __init__(self):
        # Define semantic groups for relationship standardization
        self.semantic_groups = {
            "usage": {
                "primary": "USES",
                "variants": ["USES", "UTILIZES", "APPLIES", "LEVERAGES", "OPERATES"]
            },
            "advocacy": {
                "primary": "ADVOCATES_FOR", 
                "variants": ["ADVOCATES_FOR", "PROMOTES", "CHAMPIONS", "SUPPORTS", "ENDORSES"]
            },
            "skepticism": {
                "primary": "SKEPTICAL_OF",
                "variants": ["SKEPTICAL_OF", "DOUBTS", "QUESTIONS", "CONCERNS_ABOUT", "CRITICAL_OF"]
            },
            "collaboration": {
                "primary": "COLLABORATES_WITH",
                "variants": ["COLLABORATES_WITH", "WORKS_WITH", "PARTNERS_WITH", "TEAMS_WITH"]
            },
            "management": {
                "primary": "MANAGES",
                "variants": ["MANAGES", "SUPERVISES", "OVERSEES", "LEADS", "DIRECTS"]
            },
            "employment": {
                "primary": "WORKS_AT",
                "variants": ["WORKS_AT", "EMPLOYED_BY", "EMPLOYS", "AFFILIATED_WITH", "BASED_AT"]
            },
            "membership": {
                "primary": "PART_OF",
                "variants": ["PART_OF", "MEMBER_OF", "BELONGS_TO", "COMPONENT_OF"]
            },
            "implementation": {
                "primary": "IMPLEMENTS",
                "variants": ["IMPLEMENTS", "DEPLOYS", "INSTALLS", "EXECUTES", "RUNS"]
            },
            "recommendation": {
                "primary": "RECOMMENDS",
                "variants": ["RECOMMENDS", "SUGGESTS", "ADVISES", "PROPOSES"]
            },
            "replacement": {
                "primary": "REPLACED_BY",
                "variants": ["REPLACED_BY", "SUPERSEDED_BY", "UPGRADED_TO", "MIGRATED_TO"]
            },
            "complementarity": {
                "primary": "COMPLEMENTS",
                "variants": ["COMPLEMENTS", "WORKS_WITH", "INTEGRATES_WITH", "PAIRS_WITH"]
            }
        }
        
        # Create reverse mapping for quick lookup
        self.variant_to_primary = {}
        for group_data in self.semantic_groups.values():
            primary = group_data["primary"]
            for variant in group_data["variants"]:
                self.variant_to_primary[variant.upper()] = primary
    
    def consolidate_relationship(self, relationship: ExtractedRelationship) -> ExtractedRelationship:
        """
        Consolidate relationship type to standard form if it matches known variants
        
        Args:
            relationship: The relationship to consolidate
            
        Returns:
            ExtractedRelationship with potentially standardized type
        """
        original_type = relationship.relationship_type.upper()
        
        # Check if this type should be standardized
        if original_type in self.variant_to_primary:
            standardized_type = self.variant_to_primary[original_type]
            
            if standardized_type != original_type:
                logger.info(f"Standardized relationship type: '{relationship.relationship_type}' → '{standardized_type}'")
                
                # Create new relationship with standardized type
                consolidated = ExtractedRelationship(
                    id=relationship.id,
                    source_entity=relationship.source_entity,
                    target_entity=relationship.target_entity,
                    relationship_type=standardized_type,
                    confidence=relationship.confidence,
                    context=relationship.context,
                    quotes=relationship.quotes,
                    metadata={
                        **relationship.metadata,
                        'original_type': relationship.relationship_type,
                        'standardized': True,
                        'semantic_group': self._get_semantic_group(standardized_type)
                    }
                )
                
                return consolidated
        
        # No standardization needed
        return relationship
    
    def get_relationship_variants(self, relationship_type: str) -> List[str]:
        """Get all variants for a relationship type"""
        relationship_type = relationship_type.upper()
        
        for group_data in self.semantic_groups.values():
            if relationship_type in [v.upper() for v in group_data["variants"]]:
                return group_data["variants"]
                
        return [relationship_type]
    
    def are_relationships_similar(self, type1: str, type2: str, 
                                threshold: float = 0.8) -> bool:
        """Check if two relationship types are semantically similar"""
        type1, type2 = type1.upper(), type2.upper()
        
        # Exact match
        if type1 == type2:
            return True
            
        # Check if they're in the same semantic group
        group1 = self._get_semantic_group(type1)
        group2 = self._get_semantic_group(type2)
        
        if group1 and group2 and group1 == group2:
            return True
            
        # String similarity fallback
        similarity = SequenceMatcher(None, type1, type2).ratio()
        return similarity >= threshold
    
    def _get_semantic_group(self, relationship_type: str) -> Optional[str]:
        """Get the semantic group for a relationship type"""
        relationship_type = relationship_type.upper()
        
        for group_name, group_data in self.semantic_groups.items():
            if relationship_type in [v.upper() for v in group_data["variants"]]:
                return group_name
                
        return None
    
    def get_primary_type(self, relationship_type: str) -> str:
        """Get the primary/standard type for a relationship"""
        return self.variant_to_primary.get(relationship_type.upper(), relationship_type)
    
    def suggest_relationship_types(self, partial_type: str, limit: int = 5) -> List[str]:
        """Suggest relationship types based on partial input"""
        partial = partial_type.upper()
        suggestions = []
        
        # Get all known types
        all_types = set()
        for group_data in self.semantic_groups.values():
            all_types.update(group_data["variants"])
        
        # Find matches
        for rel_type in all_types:
            if partial in rel_type:
                similarity = SequenceMatcher(None, partial, rel_type).ratio()
                suggestions.append((rel_type, similarity))
        
        # Sort by similarity and return top matches
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [rel_type for rel_type, _ in suggestions[:limit]]
    
    def validate_relationship_type(self, relationship_type: str, 
                                 source_entity_type: str, 
                                 target_entity_type: str) -> Dict[str, Any]:
        """
        Validate if a relationship type makes sense between given entity types
        
        Returns validation result with recommendations
        """
        # Define typical relationship patterns
        typical_patterns = {
            ("Person", "Organization"): ["WORKS_AT", "AFFILIATED_WITH", "PART_OF"],
            ("Person", "Tool"): ["USES", "ADVOCATES_FOR", "SKEPTICAL_OF"],
            ("Person", "Method"): ["USES", "IMPLEMENTS", "ADVOCATES_FOR", "SKEPTICAL_OF"],
            ("Person", "Person"): ["MANAGES", "COLLABORATES_WITH", "RECOMMENDS"],
            ("Organization", "Organization"): ["PART_OF", "PARTNERS_WITH", "COMPETES_WITH"],
            ("Tool", "Tool"): ["COMPLEMENTS", "REPLACED_BY", "INTEGRATES_WITH"],
            ("Method", "Organization"): ["IMPLEMENTED_AT", "USED_BY"]
        }
        
        # Normalize entity types
        source_norm = self._normalize_entity_type(source_entity_type)
        target_norm = self._normalize_entity_type(target_entity_type)
        
        # Check typical patterns
        pattern_key = (source_norm, target_norm)
        reverse_pattern_key = (target_norm, source_norm)
        
        expected_types = (typical_patterns.get(pattern_key, []) + 
                         typical_patterns.get(reverse_pattern_key, []))
        
        # Check if current type is expected
        is_typical = relationship_type.upper() in [t.upper() for t in expected_types]
        
        # Get standardized type
        standardized_type = self.get_primary_type(relationship_type)
        
        result = {
            "is_valid": True,  # We're permissive by default
            "is_typical": is_typical,
            "standardized_type": standardized_type,
            "expected_types": expected_types,
            "confidence": 1.0 if is_typical else 0.7,
            "warnings": []
        }
        
        if not is_typical and expected_types:
            result["warnings"].append(
                f"Unusual relationship '{relationship_type}' between {source_entity_type} and {target_entity_type}. "
                f"Expected: {', '.join(expected_types[:3])}"
            )
        
        return result
    
    def _normalize_entity_type(self, entity_type: str) -> str:
        """Normalize entity type to standard form"""
        entity_type = entity_type.lower()
        
        # Map variations to standard types
        type_mapping = {
            "person": "Person",
            "people": "Person", 
            "researcher": "Person",
            "employee": "Person",
            "organization": "Organization",
            "org": "Organization",
            "company": "Organization",
            "institution": "Organization",
            "tool": "Tool",
            "software": "Tool",
            "platform": "Tool",
            "system": "Tool",
            "method": "Method",
            "methodology": "Method",
            "technique": "Method",
            "approach": "Method"
        }
        
        return type_mapping.get(entity_type, entity_type.title())