"""
Enhanced extraction pipeline with integrated validation system.

This module wraps the existing multi_pass_extractor with intelligent validation,
consolidation, and quality control capabilities.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .multi_pass_extractor import MultiPassExtractor, ExtractionResult, InterviewContext
from .extraction_schemas import ExtractedEntity, ExtractedRelationship, ExtractedCode
from ..validation import (
    EntityConsolidator, RelationshipConsolidator, QualityValidator,
    ValidationConfig, ValidationMode, ValidationResult
)
from ..utils.error_handler import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class ValidationStats:
    """Statistics from validation process"""
    entities_processed: int = 0
    entities_merged: int = 0
    entities_rejected: int = 0
    relationships_processed: int = 0
    relationships_standardized: int = 0
    relationships_rejected: int = 0
    quality_issues_found: int = 0
    validation_time_ms: int = 0


class ValidatedExtractor:
    """
    Enhanced extractor with validation, consolidation, and quality control
    """
    
    def __init__(self, 
                 base_extractor: MultiPassExtractor,
                 validation_config: ValidationConfig = None):
        """
        Initialize validated extractor
        
        Args:
            base_extractor: The underlying extraction system
            validation_config: Validation configuration (defaults to hybrid mode)
        """
        # FAIL-FAST: Runtime parameter validation
        if not isinstance(base_extractor, MultiPassExtractor):
            raise TypeError(f"base_extractor must be MultiPassExtractor, got {type(base_extractor)}")
        if validation_config is not None and not isinstance(validation_config, ValidationConfig):
            raise TypeError(f"validation_config must be ValidationConfig, got {type(validation_config)}")
        
        self.base_extractor = base_extractor
        self.validation_config = validation_config or ValidationConfig.production_research_config()
        
        # Initialize validation components
        self.entity_consolidator = EntityConsolidator(
            consolidation_threshold=self.validation_config.consolidation_threshold
        )
        self.relationship_consolidator = RelationshipConsolidator()
        self.quality_validator = QualityValidator(
            auto_approve_threshold=self.validation_config.confidence_auto_approve,
            review_threshold=self.validation_config.confidence_flag_review,
            validation_threshold=self.validation_config.confidence_require_validation
        )
        
        logger.info(f"Initialized ValidatedExtractor with {self.validation_config.entities.value} entity mode "
                   f"and {self.validation_config.relationships.value} relationship mode")
    
    async def extract_from_interview(self, context: InterviewContext) -> Tuple[List[ExtractionResult], ValidationStats]:
        """
        Run complete extraction with validation
        
        Args:
            context: Interview context
            
        Returns:
            Tuple of (extraction_results, validation_stats)
        """
        start_time = datetime.utcnow()
        
        # Run base extraction
        logger.info("Running base extraction...")
        extraction_results = await self.base_extractor.extract_from_interview(context)
        
        # Apply validation and consolidation
        logger.info("Applying validation and consolidation...")
        validated_results, validation_stats = await self._validate_and_consolidate(
            extraction_results, context
        )
        
        # Calculate validation time
        validation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        validation_stats.validation_time_ms = int(validation_time)
        
        logger.info(f"Validation completed in {validation_time:.0f}ms: "
                   f"{validation_stats.entities_processed} entities, "
                   f"{validation_stats.relationships_processed} relationships processed")
        
        return validated_results, validation_stats
    
    async def _validate_and_consolidate(self, 
                                      extraction_results: List[ExtractionResult],
                                      context: InterviewContext) -> Tuple[List[ExtractionResult], ValidationStats]:
        """
        Apply validation and consolidation to extraction results
        """
        stats = ValidationStats()
        validated_results = []
        
        # Collect all entities and relationships across results
        all_entities = []
        all_relationships = []
        all_codes = []
        
        for result in extraction_results:
            # Convert to ExtractedEntity objects for validation
            for entity_id, entity_data in result.entities_found.items():
                # FAIL-FAST: Validate required fields before creating entity
                name = entity_data.get('name', '').strip()
                entity_type = entity_data.get('type', '').strip()
                
                if not name:
                    raise ValidationError(f"Entity {entity_id} missing required 'name' field")
                if not entity_type:
                    raise ValidationError(f"Entity {entity_id} missing required 'type' field")
                if not entity_id or not str(entity_id).strip():
                    raise ValidationError(f"Entity missing valid 'id' field")
                
                # Validate confidence score if provided
                confidence = entity_data.get('confidence', 0.8)
                if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
                    raise ValidationError(f"Entity {entity_id} has invalid confidence score: {confidence}")
                
                # Generate context if missing - don't fail for empty context
                entity_context = entity_data.get('context', '').strip()
                if not entity_context:
                    entity_context = f"Found in {getattr(context, 'filename', str(context))}"
                
                entity = ExtractedEntity(
                    id=entity_id,
                    name=entity_data['name'],  # Required field, no default
                    type=entity_data['type'],  # Required field, no default
                    confidence=entity_data.get('confidence', 0.8),
                    context=entity_context,  # Use the context we just generated/retrieved
                    quotes=entity_data.get('quotes', [])
                )
                all_entities.append((entity_id, entity))
            
            # Convert to ExtractedRelationship objects for validation
            for i, rel_data in enumerate(result.relationships_found):
                # FAIL-FAST: Validate required fields for relationships
                source_entity = rel_data.get('source_entity', '').strip()
                target_entity = rel_data.get('target_entity', '').strip()
                relationship_type = rel_data.get('relationship_type', rel_data.get('type', '')).strip()
                
                if not source_entity:
                    raise ValidationError(f"Relationship {i} missing required 'source_entity' field")
                if not target_entity:
                    raise ValidationError(f"Relationship {i} missing required 'target_entity' field")
                if not relationship_type:
                    raise ValidationError(f"Relationship {i} missing required 'relationship_type' field")
                
                # Validate confidence score
                confidence = rel_data.get('confidence', 0.8)
                if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
                    raise ValidationError(f"Relationship {i} has invalid confidence score: {confidence}")
                
                # Validate context
                rel_context_str = rel_data.get('context', '').strip()
                if not rel_context_str:
                    raise ValidationError(f"Relationship {i} missing required 'context' field")
                
                relationship = ExtractedRelationship(
                    id=rel_data.get('id', f"rel_{i}_{getattr(context, 'interview_id', 'unknown')}"),
                    source_entity=rel_data['source_entity'],  # Required field, no default
                    target_entity=rel_data['target_entity'],  # Required field, no default
                    relationship_type=rel_data.get('relationship_type') or rel_data.get('type', 'RELATED_TO'),
                    confidence=rel_data.get('confidence', 0.8),
                    context=rel_data.get('context', f"Found in {getattr(context, 'filename', str(context))}"),
                    quotes=rel_data.get('quotes', [])
                )
                all_relationships.append(relationship)
            
            # Convert to ExtractedCode objects for validation
            for code_id, code_data in result.codes_found.items():
                # FAIL-FAST: Validate required fields for codes
                name = code_data.get('name', code_id).strip()
                description = code_data.get('description', '').strip()
                
                if not name:
                    raise ValidationError(f"Code {code_id} missing required 'name' field")
                if not description:
                    raise ValidationError(f"Code {code_id} missing required 'description' field")
                if not code_id or not str(code_id).strip():
                    raise ValidationError(f"Code missing valid 'id' field")
                
                # Validate frequency
                frequency = code_data.get('frequency', 1)
                if not isinstance(frequency, int) or frequency < 0:
                    raise ValidationError(f"Code {code_id} has invalid frequency: {frequency}")
                
                # Validate confidence score
                confidence = code_data.get('confidence', 0.8)
                if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
                    raise ValidationError(f"Code {code_id} has invalid confidence score: {confidence}")
                
                all_codes.append((code_id, code_data))
        
        # Phase 1: Entity validation and consolidation
        validated_entities = await self._validate_entities(all_entities, stats)
        
        # Phase 2: Relationship validation and standardization
        validated_relationships = await self._validate_relationships(all_relationships, stats)
        
        # Phase 3: Rebuild extraction results with validated data
        validated_result = ExtractionResult(
            pass_number=1,  # Consolidated result
            entities_found={eid: self._entity_to_dict(entity) for eid, entity in validated_entities},
            relationships_found=[self._relationship_to_dict(rel) for rel in validated_relationships],
            codes_found={cid: code_data for cid, code_data in all_codes},
            success=True,
            metadata={
                'validation_applied': True,
                'validation_config': self.validation_config.__dict__,
                'validation_stats': stats.__dict__
            }
        )
        
        return [validated_result], stats
    
    async def _validate_entities(self, 
                                entities: List[Tuple[str, ExtractedEntity]], 
                                stats: ValidationStats) -> List[Tuple[str, ExtractedEntity]]:
        """Validate and consolidate entities"""
        validated_entities = []
        processed_entities = []
        
        for entity_id, entity in entities:
            stats.entities_processed += 1
            
            # Apply entity type validation based on mode
            if not self._is_entity_type_allowed(entity.type):
                logger.debug(f"Rejected entity '{entity.name}' - type '{entity.type}' not allowed in {self.validation_config.entities.value} mode")
                stats.entities_rejected += 1
                continue
            
            # Quality validation
            quality_report = self.quality_validator.validate_entity(entity)
            
            if quality_report.validation_result == ValidationResult.AUTO_REJECT:
                logger.debug(f"Rejected entity '{entity.name}' - failed quality validation")
                stats.entities_rejected += 1
                stats.quality_issues_found += len(quality_report.issues)
                continue
            
            # Log quality issues
            if quality_report.issues:
                stats.quality_issues_found += len(quality_report.issues)
                for issue in quality_report.issues:
                    if issue.severity == "error":
                        logger.warning(f"Entity '{entity.name}': {issue.message}")
                    else:
                        logger.debug(f"Entity '{entity.name}': {issue.message}")
            
            # Consolidation check
            if self.validation_config.auto_merge_similar:
                consolidation_result = self.entity_consolidator.consolidate_entities(
                    entity, [e for _, e in processed_entities]
                )
                
                if consolidation_result.should_merge:
                    # Replace the entity we would have merged with
                    for i, (existing_id, existing_entity) in enumerate(processed_entities):
                        if existing_entity.name == consolidation_result.merged_entity.name:
                            processed_entities[i] = (existing_id, consolidation_result.merged_entity)
                            break
                    
                    logger.info(f"Merged entity: '{entity.name}' → '{consolidation_result.merged_entity.name}'")
                    stats.entities_merged += 1
                    continue
            
            # Add entity to processed list
            processed_entities.append((entity_id, entity))
        
        return processed_entities
    
    async def _validate_relationships(self, 
                                    relationships: List[ExtractedRelationship],
                                    stats: ValidationStats) -> List[ExtractedRelationship]:
        """Validate and standardize relationships"""
        validated_relationships = []
        
        for relationship in relationships:
            stats.relationships_processed += 1
            
            # Apply relationship type validation based on mode
            if not self._is_relationship_type_allowed(relationship.relationship_type):
                logger.debug(f"Rejected relationship '{relationship.relationship_type}' - not allowed in {self.validation_config.relationships.value} mode")
                stats.relationships_rejected += 1
                continue
            
            # Quality validation
            quality_report = self.quality_validator.validate_relationship(relationship)
            
            if quality_report.validation_result == ValidationResult.AUTO_REJECT:
                logger.debug(f"Rejected relationship '{relationship.source_entity} -> {relationship.target_entity}' - failed quality validation")
                stats.relationships_rejected += 1
                stats.quality_issues_found += len(quality_report.issues)
                continue
            
            # Log quality issues
            if quality_report.issues:
                stats.quality_issues_found += len(quality_report.issues)
                for issue in quality_report.issues:
                    if issue.severity == "error":
                        logger.warning(f"Relationship '{relationship.source_entity} -> {relationship.target_entity}': {issue.message}")
                    else:
                        logger.debug(f"Relationship '{relationship.source_entity} -> {relationship.target_entity}': {issue.message}")
            
            # Relationship consolidation/standardization
            consolidated_relationship = self.relationship_consolidator.consolidate_relationship(relationship)
            
            if consolidated_relationship.relationship_type != relationship.relationship_type:
                stats.relationships_standardized += 1
            
            validated_relationships.append(consolidated_relationship)
        
        return validated_relationships
    
    def _is_entity_type_allowed(self, entity_type: str) -> bool:
        """Check if entity type is allowed based on validation mode"""
        if self.validation_config.entities == ValidationMode.OPEN:
            return True
        
        if self.validation_config.entities == ValidationMode.CLOSED:
            return entity_type in self.validation_config.standard_entity_types
        
        # Hybrid mode - allow both standard and discovered
        return True
    
    def _is_relationship_type_allowed(self, relationship_type: str) -> bool:
        """Check if relationship type is allowed based on validation mode"""
        if self.validation_config.relationships == ValidationMode.OPEN:
            return True
        
        if self.validation_config.relationships == ValidationMode.CLOSED:
            return relationship_type.upper() in [rt.upper() for rt in self.validation_config.standard_relationship_types]
        
        # Hybrid mode - allow both standard and discovered
        return True
    
    def _entity_to_dict(self, entity: ExtractedEntity) -> Dict[str, Any]:
        """Convert ExtractedEntity back to dict format"""
        return {
            'id': entity.id,
            'name': entity.name,
            'type': entity.type,
            'properties': entity.properties,
            'quotes': entity.quotes,
            'confidence': entity.confidence,
            'metadata': entity.metadata,
            'context': entity.context
        }
    
    def _relationship_to_dict(self, relationship: ExtractedRelationship) -> Dict[str, Any]:
        """Convert ExtractedRelationship back to dict format"""
        return {
            'id': relationship.id,
            'source_entity': relationship.source_entity,
            'target_entity': relationship.target_entity,
            'relationship_type': relationship.relationship_type,
            'type': relationship.relationship_type,  # Keep both for compatibility
            'confidence': relationship.confidence,
            'context': relationship.context,
            'quotes': relationship.quotes,
            'metadata': relationship.metadata
        }
    
    def update_validation_config(self, new_config: ValidationConfig):
        """Update validation configuration"""
        self.validation_config = new_config
        
        # Update component configurations
        self.entity_consolidator.consolidation_threshold = new_config.consolidation_threshold
        self.quality_validator = QualityValidator(
            auto_approve_threshold=new_config.confidence_auto_approve,
            review_threshold=new_config.confidence_flag_review,
            validation_threshold=new_config.confidence_require_validation
        )
        
        logger.info(f"Updated validation config to {new_config.entities.value} entity mode "
                   f"and {new_config.relationships.value} relationship mode")