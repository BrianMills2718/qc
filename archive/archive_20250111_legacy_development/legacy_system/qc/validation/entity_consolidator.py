"""
Entity consolidation logic for intelligent merging of similar entities.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher
import re

from ..extraction.extraction_schemas import ExtractedEntity

logger = logging.getLogger(__name__)


@dataclass
class ConsolidationResult:
    """Result of entity consolidation attempt"""
    should_merge: bool
    confidence: float
    reason: str
    merged_entity: Optional[ExtractedEntity] = None
    similarity_scores: Dict[str, float] = None


class EntityConsolidator:
    """Intelligently consolidates similar entities to maintain consistency"""
    
    def __init__(self, consolidation_threshold: float = 0.85):
        self.consolidation_threshold = consolidation_threshold
        
    def consolidate_entities(self, new_entity: ExtractedEntity, 
                           existing_entities: List[ExtractedEntity]) -> ConsolidationResult:
        """
        Intelligently merge similar entities to maintain consistency
        
        Args:
            new_entity: Entity being processed
            existing_entities: Previously processed entities
            
        Returns:
            ConsolidationResult indicating if merge should occur
        """
        best_match = None
        best_score = 0.0
        best_scores = {}
        
        for existing in existing_entities:
            # Skip if different types (unless both are unknown/generic)
            if not self._types_compatible(new_entity.type, existing.type):
                continue
                
            # Calculate similarity scores
            name_similarity = self._calculate_name_similarity(new_entity.name, existing.name)
            semantic_similarity = self._calculate_semantic_similarity(
                new_entity.properties, existing.properties
            )
            context_similarity = self._calculate_context_overlap(
                new_entity.quotes, existing.quotes
            )
            
            # Combined similarity score
            total_similarity = (
                name_similarity * 0.4 + 
                semantic_similarity * 0.4 + 
                context_similarity * 0.2
            )
            
            scores = {
                'name': name_similarity,
                'semantic': semantic_similarity, 
                'context': context_similarity,
                'total': total_similarity
            }
            
            if total_similarity > best_score:
                best_score = total_similarity
                best_match = existing
                best_scores = scores
        
        # Determine if we should merge
        should_merge = best_score > self.consolidation_threshold
        
        if should_merge and best_match:
            merged_entity = self._merge_entities(new_entity, best_match)
            reason = f"High similarity ({best_score:.2f}) with existing entity '{best_match.name}'"
        else:
            merged_entity = None
            reason = f"No similar entity found (best score: {best_score:.2f})"
            
        return ConsolidationResult(
            should_merge=should_merge,
            confidence=best_score,
            reason=reason,
            merged_entity=merged_entity,
            similarity_scores=best_scores
        )
    
    def _types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two entity types are compatible for merging"""
        # Exact match
        if type1 == type2:
            return True
            
        # Unknown/generic types can merge with anything
        if type1 in ["Unknown", "Generic"] or type2 in ["Unknown", "Generic"]:
            return True
            
        # Define compatible type groups
        person_types = {"Person", "Researcher", "Employee", "Manager", "Director"}
        org_types = {"Organization", "Company", "Institution", "Department", "Center"}
        tool_types = {"Tool", "Software", "Platform", "System", "API"}
        method_types = {"Method", "Technique", "Approach", "Framework", "Methodology"}
        
        type_groups = [person_types, org_types, tool_types, method_types]
        
        for group in type_groups:
            if type1 in group and type2 in group:
                return True
                
        return False
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between entity names"""
        if not name1 or not name2:
            return 0.0
            
        # Normalize names
        norm1 = self._normalize_name(name1)
        norm2 = self._normalize_name(name2)
        
        # Exact match after normalization
        if norm1 == norm2:
            return 1.0
            
        # Sequence matching
        seq_match = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Check for substring containment
        if norm1 in norm2 or norm2 in norm1:
            substring_bonus = 0.3
        else:
            substring_bonus = 0.0
            
        # Check for common abbreviations/variations
        abbrev_bonus = self._check_abbreviation_match(norm1, norm2)
        
        return min(1.0, seq_match + substring_bonus + abbrev_bonus)
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        if not name:
            return ""
            
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common prefixes/suffixes
        normalized = re.sub(r'^(dr\.?|prof\.?|mr\.?|ms\.?|mrs\.?)\s+', '', normalized)
        normalized = re.sub(r'\s+(jr\.?|sr\.?|ii|iii|iv)$', '', normalized)
        
        # Remove punctuation and extra whitespace
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _check_abbreviation_match(self, name1: str, name2: str) -> float:
        """Check for common abbreviation patterns"""
        # Check if one is abbreviation of the other
        words1 = name1.split()
        words2 = name2.split()
        
        # Simple abbreviation check (first letters)
        if len(words1) > 1 and len(words2) == 1:
            abbrev = ''.join(word[0] for word in words1 if word)
            if abbrev == words2[0]:
                return 0.4
                
        if len(words2) > 1 and len(words1) == 1:
            abbrev = ''.join(word[0] for word in words2 if word)
            if abbrev == words1[0]:
                return 0.4
                
        return 0.0
    
    def _calculate_semantic_similarity(self, props1: Dict[str, Any], 
                                     props2: Dict[str, Any]) -> float:
        """Calculate semantic similarity between entity properties"""
        if not props1 and not props2:
            return 1.0
            
        if not props1 or not props2:
            return 0.2  # Some penalty but not zero
            
        # Get all property keys
        all_keys = set(props1.keys()) | set(props2.keys())
        if not all_keys:
            return 1.0
            
        matches = 0
        total_comparisons = 0
        
        for key in all_keys:
            if key in props1 and key in props2:
                val1, val2 = props1[key], props2[key]
                
                # String comparison
                if isinstance(val1, str) and isinstance(val2, str):
                    similarity = SequenceMatcher(None, val1.lower(), val2.lower()).ratio()
                    matches += similarity
                # Exact value match
                elif val1 == val2:
                    matches += 1.0
                # Type mismatch
                else:
                    matches += 0.2
                    
                total_comparisons += 1
            else:
                # Property exists in only one entity
                total_comparisons += 1
                matches += 0.1
                
        return matches / total_comparisons if total_comparisons > 0 else 1.0
    
    def _calculate_context_overlap(self, quotes1: List[str], 
                                 quotes2: List[str]) -> float:
        """Calculate overlap between supporting quotes/context"""
        if not quotes1 and not quotes2:
            return 1.0
            
        if not quotes1 or not quotes2:
            return 0.3  # Some penalty but entities might have different contexts
            
        # Calculate quote similarity
        max_similarities = []
        
        for quote1 in quotes1:
            best_similarity = 0.0
            for quote2 in quotes2:
                similarity = SequenceMatcher(None, quote1.lower(), quote2.lower()).ratio()
                best_similarity = max(best_similarity, similarity)
            max_similarities.append(best_similarity)
            
        # Average of best similarities
        if max_similarities:
            return sum(max_similarities) / len(max_similarities)
        
        return 0.0
    
    def _merge_entities(self, entity1: ExtractedEntity, 
                       entity2: ExtractedEntity) -> ExtractedEntity:
        """Merge two entities intelligently"""
        # Use the entity with higher confidence as base
        if entity1.confidence >= entity2.confidence:
            primary, secondary = entity1, entity2
        else:
            primary, secondary = entity2, entity1
            
        # Create merged entity
        merged = ExtractedEntity(
            name=primary.name,  # Keep primary name
            type=primary.type if primary.type != "Unknown" else secondary.type,
            properties={**secondary.properties, **primary.properties},  # Primary overwrites
            quotes=list(set(primary.quotes + secondary.quotes)),  # Combine unique quotes
            confidence=max(primary.confidence, secondary.confidence),
            metadata={
                **secondary.metadata,
                **primary.metadata,
                'merged_from': [secondary.name],
                'merge_confidence': self._calculate_name_similarity(entity1.name, entity2.name)
            }
        )
        
        logger.info(f"Merged entities: '{entity1.name}' + '{entity2.name}' → '{merged.name}'")
        
        return merged