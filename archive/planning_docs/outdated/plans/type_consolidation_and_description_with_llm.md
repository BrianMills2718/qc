# Type Consolidation and Description with LLM

**Status**: Approved for Implementation  
**Priority**: High  
**Estimated Effort**: 2-3 days implementation + testing

## Overview

Enhance the qualitative coding system to automatically consolidate discovered entity and relationship types using LLM semantic understanding, while providing clear definitions for all types. This replaces the current string-similarity consolidation with intelligent semantic grouping.

## Problem Statement

### Current Issues
1. **Semantic Confusion**: Outputs like "Google USES Mark Johnson" instead of "Mark Johnson WORKS_AT Google"
2. **Type Proliferation**: Similar types not consolidated (e.g., "API Gateway", "Service Mesh", "Load Balancer" all separate)
3. **No Definitions**: Users must infer meaning from type names without semantic context
4. **Limited Consolidation**: Current string-matching consolidation misses semantic similarities

### Success Criteria
- Clear, meaningful type definitions in all outputs
- Intelligent consolidation of semantically similar types
- Consistent type usage across validation modes (open/closed/hybrid)
- Preserved system performance and reliability

## Architecture Decision

**Selected Approach**: Post-Processing Consolidation (Option A)

**Rationale**:
- Clean separation from existing extraction pipeline (90% confidence, lowest risk)
- Complete session context for better consolidation decisions
- Easy to test, debug, and rollback if needed
- Minimal disruption to working extraction system

## Detailed Implementation Plan

### Phase 1: Schema and Infrastructure (Days 1-2)

#### 1.1 Schema Enhancement
**File**: `qc/extraction/extraction_schemas.py`

Add definition fields to existing schemas:
```python
class ExtractedEntity(BaseModel):
    name: str = Field(..., description="Name or title of the entity")
    type: str = Field(..., description="Type of entity (Person, Organization, etc.)")
    type_definition: str = ""  # NEW: LLM-generated semantic definition
    
    # ... existing fields unchanged

class ExtractedRelationship(BaseModel):
    source_entity: str = Field(..., description="Name of source entity")
    target_entity: str = Field(..., description="Name of target entity") 
    relationship_type: str = Field(..., description="Type of relationship")
    relationship_definition: str = ""  # NEW: LLM-generated semantic definition
    
    # ... existing fields unchanged
```

**Implementation Notes**:
- Fields default to empty string for backward compatibility
- No Gemini schema compatibility issues (empty strings allowed)
- Existing validation logic unaffected

#### 1.2 Consolidation Request/Response Schemas
**File**: `qc/consolidation/consolidation_schemas.py` (NEW)

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class TypeDefinition(BaseModel):
    """Single type with definition"""
    type_name: str = Field(..., description="Name of the type")
    definition: str = Field(..., description="Semantic definition of the type")
    frequency: int = Field(default=1, description="How many times this type appeared")

class ConsolidationRequest(BaseModel):
    """Request format for LLM consolidation"""
    entity_types: List[TypeDefinition] = Field(..., description="Discovered entity types")
    relationship_types: List[TypeDefinition] = Field(..., description="Discovered relationship types") 
    predefined_entity_types: List[TypeDefinition] = Field(default=[], description="Standard entity types")
    predefined_relationship_types: List[TypeDefinition] = Field(default=[], description="Standard relationship types")
    validation_mode: str = Field(..., description="open, closed, or hybrid")

class ConsolidatedType(BaseModel):
    """Single consolidated type result"""
    canonical_name: str = Field(..., description="Canonical type name to use")
    definition: str = Field(..., description="Clear semantic definition")
    variants: List[str] = Field(..., description="Original type names that map to this canonical type")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")

class ConsolidationResponse(BaseModel):
    """LLM response format"""
    consolidated_entities: List[ConsolidatedType] = Field(..., description="Consolidated entity types")
    consolidated_relationships: List[ConsolidatedType] = Field(..., description="Consolidated relationship types")
    summary: str = Field(..., description="Brief summary of consolidation changes made")
```

#### 1.3 LLM Consolidator Service
**File**: `qc/consolidation/llm_consolidator.py` (NEW)

```python
import logging
from typing import List, Dict, Any
from ..core.native_gemini_client import NativeGeminiClient
from .consolidation_schemas import ConsolidationRequest, ConsolidationResponse

logger = logging.getLogger(__name__)

class LLMConsolidator:
    """LLM-powered semantic type consolidation"""
    
    def __init__(self, gemini_client: NativeGeminiClient):
        self.client = gemini_client
    
    async def consolidate_session_types(self, request: ConsolidationRequest) -> ConsolidationResponse:
        """
        Consolidate discovered types using LLM semantic understanding
        
        Args:
            request: ConsolidationRequest with discovered types and validation mode
            
        Returns:
            ConsolidationResponse with consolidated types and definitions
        """
        
        # Build consolidation prompt based on validation mode
        prompt = self._build_consolidation_prompt(request)
        
        # Call Gemini with structured output
        try:
            response = await self.client.generate_structured_content(
                prompt=prompt,
                response_schema=ConsolidationResponse
            )
            
            logger.info(f"Consolidated {len(request.entity_types)} entity types into "
                       f"{len(response.consolidated_entities)} canonical types")
            logger.info(f"Consolidated {len(request.relationship_types)} relationship types into "
                       f"{len(response.consolidated_relationships)} canonical types")
            
            return response
            
        except Exception as e:
            logger.error(f"LLM consolidation failed: {e}")
            # Fallback: return original types with basic definitions
            return self._create_fallback_response(request)
    
    def _build_consolidation_prompt(self, request: ConsolidationRequest) -> str:
        """Build mode-specific consolidation prompt"""
        
        base_prompt = """You are a qualitative research coding specialist. Your task is to consolidate discovered entity and relationship types into canonical forms with clear semantic definitions.

VALIDATION MODE: {validation_mode}

DISCOVERED ENTITY TYPES:
{entity_types}

DISCOVERED RELATIONSHIP TYPES:  
{relationship_types}

{predefined_section}

CONSOLIDATION RULES:
1. Group semantically similar types together (e.g., "API Gateway", "Service Mesh" → "Infrastructure Component")
2. Provide clear, precise definitions for each canonical type
3. Ensure relationship directions make logical sense (e.g., "Person WORKS_AT Organization", not "Organization USES Person")
4. In hybrid/closed modes, prefer predefined types when semantically equivalent
5. Maintain semantic precision - don't over-consolidate distinct concepts

OUTPUT REQUIREMENTS:
- canonical_name: Clear, professional type name
- definition: 2-3 sentence semantic definition
- variants: List of original types consolidated into this canonical type
- confidence: Your confidence in this consolidation (0.0-1.0)

Generate consolidated types that will help researchers understand their data clearly."""

        # Format entity types
        entity_list = "\n".join([
            f"- \"{t.type_name}\" (frequency: {t.frequency}): {t.definition}"
            for t in request.entity_types
        ])
        
        # Format relationship types
        relationship_list = "\n".join([
            f"- \"{t.type_name}\" (frequency: {t.frequency}): {t.definition}"
            for t in request.relationship_types
        ])
        
        # Handle predefined types for hybrid/closed modes
        predefined_section = ""
        if request.validation_mode in ["hybrid", "closed"]:
            if request.predefined_entity_types or request.predefined_relationship_types:
                predefined_section = "PREDEFINED STANDARD TYPES (prefer these when semantically equivalent):\n"
                
                if request.predefined_entity_types:
                    predefined_section += "Entities:\n" + "\n".join([
                        f"- \"{t.type_name}\": {t.definition}" for t in request.predefined_entity_types
                    ]) + "\n"
                    
                if request.predefined_relationship_types:
                    predefined_section += "Relationships:\n" + "\n".join([
                        f"- \"{t.type_name}\": {t.definition}" for t in request.predefined_relationship_types
                    ]) + "\n"
        
        return base_prompt.format(
            validation_mode=request.validation_mode,
            entity_types=entity_list,
            relationship_types=relationship_list,
            predefined_section=predefined_section
        )
    
    def _create_fallback_response(self, request: ConsolidationRequest) -> ConsolidationResponse:
        """Create fallback response if LLM consolidation fails"""
        logger.warning("Using fallback consolidation - no semantic grouping applied")
        
        # Return original types as individual consolidated types
        consolidated_entities = [
            ConsolidatedType(
                canonical_name=t.type_name,
                definition=t.definition or f"Entity of type {t.type_name}",
                variants=[t.type_name],
                confidence=0.5
            ) for t in request.entity_types
        ]
        
        consolidated_relationships = [
            ConsolidatedType(
                canonical_name=t.type_name,
                definition=t.definition or f"Relationship of type {t.type_name}",
                variants=[t.type_name],
                confidence=0.5
            ) for t in request.relationship_types
        ]
        
        return ConsolidationResponse(
            consolidated_entities=consolidated_entities,
            consolidated_relationships=consolidated_relationships,
            summary="Fallback consolidation applied - LLM consolidation failed"
        )
```

### Phase 2: Integration Point (Day 2)

#### 2.1 CLI Integration 
**File**: `qc/cli.py`

Add consolidation step after all interviews processed:

```python
# Add import
from .consolidation.llm_consolidator import LLMConsolidator
from .consolidation.consolidation_schemas import ConsolidationRequest, TypeDefinition

class QualitativeCodingCLI:
    def __init__(self):
        # ... existing initialization
        self.consolidator = LLMConsolidator(self.extractor.llm_client)
    
    async def analyze_interviews(self, files: List[str], validation_mode: str = "hybrid", 
                               enable_validation: bool = True, output: str = None) -> str:
        """Enhanced with LLM consolidation"""
        
        # ... existing extraction logic unchanged until after all interviews processed
        
        # NEW: Collect all discovered types from session
        if enable_validation:
            discovered_types = self._collect_session_types(all_entities, all_relationships)
            
            # Perform LLM consolidation
            logger.info("Performing LLM-based type consolidation...")
            consolidation_request = self._build_consolidation_request(
                discovered_types, validation_mode
            )
            
            consolidation_response = await self.consolidator.consolidate_session_types(
                consolidation_request
            )
            
            # Apply consolidations to stored data
            await self._apply_consolidations_to_data(consolidation_response, session_id)
            
            # Update entities and relationships with consolidated types
            all_entities, all_relationships = await self._fetch_consolidated_data(session_id)
        
        # ... existing export logic unchanged
    
    def _collect_session_types(self, entities: List[Dict], relationships: List[Dict]) -> Dict:
        """Collect and count all discovered types from session"""
        entity_type_counts = {}
        relationship_type_counts = {}
        
        # Count entity types
        for entity in entities:
            entity_type = entity.get('type', 'Unknown')
            if entity_type not in entity_type_counts:
                entity_type_counts[entity_type] = {
                    'count': 0,
                    'definition': entity.get('type_definition', '')
                }
            entity_type_counts[entity_type]['count'] += 1
        
        # Count relationship types  
        for relationship in relationships:
            rel_type = relationship.get('relationship_type', 'RELATED_TO')
            if rel_type not in relationship_type_counts:
                relationship_type_counts[rel_type] = {
                    'count': 0,
                    'definition': relationship.get('relationship_definition', '')
                }
            relationship_type_counts[rel_type]['count'] += 1
        
        return {
            'entity_types': entity_type_counts,
            'relationship_types': relationship_type_counts
        }
    
    def _build_consolidation_request(self, discovered_types: Dict, validation_mode: str) -> ConsolidationRequest:
        """Build consolidation request from discovered types"""
        
        # Convert to TypeDefinition objects
        entity_types = [
            TypeDefinition(
                type_name=type_name,
                definition=type_data['definition'],
                frequency=type_data['count']
            )
            for type_name, type_data in discovered_types['entity_types'].items()
        ]
        
        relationship_types = [
            TypeDefinition(
                type_name=type_name,
                definition=type_data['definition'], 
                frequency=type_data['count']
            )
            for type_name, type_data in discovered_types['relationship_types'].items()
        ]
        
        # Add predefined types for hybrid/closed modes
        predefined_entities = []
        predefined_relationships = []
        
        if validation_mode in ['hybrid', 'closed']:
            predefined_entities = self._get_predefined_entity_types()
            predefined_relationships = self._get_predefined_relationship_types()
        
        return ConsolidationRequest(
            entity_types=entity_types,
            relationship_types=relationship_types,
            predefined_entity_types=predefined_entities,
            predefined_relationship_types=predefined_relationships,
            validation_mode=validation_mode
        )
    
    async def _apply_consolidations_to_data(self, consolidation: ConsolidationResponse, session_id: str):
        """Apply consolidation mappings to Neo4j data"""
        
        # Create type mappings
        entity_mappings = {}
        relationship_mappings = {}
        
        for consolidated in consolidation.consolidated_entities:
            for variant in consolidated.variants:
                entity_mappings[variant] = {
                    'canonical_type': consolidated.canonical_name,
                    'definition': consolidated.definition
                }
        
        for consolidated in consolidation.consolidated_relationships:
            for variant in consolidated.variants:
                relationship_mappings[variant] = {
                    'canonical_type': consolidated.canonical_name,
                    'definition': consolidated.definition
                }
        
        # Update Neo4j data
        await self._update_neo4j_types(entity_mappings, relationship_mappings, session_id)
    
    async def _update_neo4j_types(self, entity_mappings: Dict, relationship_mappings: Dict, session_id: str):
        """Update Neo4j with consolidated types and definitions"""
        
        # Update entity types and add definitions
        for original_type, mapping in entity_mappings.items():
            query = """
            MATCH (e:Entity)
            WHERE e.entity_type = $original_type 
              AND e.id CONTAINS $session_id
            SET e.entity_type = $canonical_type,
                e.type_definition = $definition,
                e.original_type = $original_type,
                e.consolidated = true
            RETURN count(e) as updated_count
            """
            
            result = await self.neo4j.execute_cypher(query, {
                'original_type': original_type,
                'canonical_type': mapping['canonical_type'],
                'definition': mapping['definition'],
                'session_id': session_id
            })
            
            count = result[0]['updated_count'] if result else 0
            logger.info(f"Updated {count} entities: '{original_type}' → '{mapping['canonical_type']}'")
        
        # Update relationship types and add definitions
        for original_type, mapping in relationship_mappings.items():
            query = """
            MATCH ()-[r]-()
            WHERE type(r) = $original_type
              AND (r.source_id CONTAINS $session_id OR r.target_id CONTAINS $session_id)
            SET r.relationship_definition = $definition,
                r.original_type = $original_type,
                r.consolidated = true
            WITH r, $canonical_type as new_type
            CALL apoc.refactor.setType(r, new_type) YIELD input, output
            RETURN count(output) as updated_count
            """
            
            # Note: This requires APOC plugin for dynamic relationship type changes
            # Alternative: Store canonical type as property if APOC unavailable
            
            try:
                result = await self.neo4j.execute_cypher(query, {
                    'original_type': original_type,
                    'canonical_type': mapping['canonical_type'],
                    'definition': mapping['definition'],
                    'session_id': session_id
                })
                
                count = result[0]['updated_count'] if result else 0
                logger.info(f"Updated {count} relationships: '{original_type}' → '{mapping['canonical_type']}'")
                
            except Exception as e:
                logger.warning(f"Could not update relationship type dynamically: {e}")
                # Fallback: store as property
                fallback_query = """
                MATCH ()-[r]-()
                WHERE type(r) = $original_type
                  AND (r.source_id CONTAINS $session_id OR r.target_id CONTAINS $session_id)
                SET r.canonical_relationship_type = $canonical_type,
                    r.relationship_definition = $definition,
                    r.original_type = $original_type,
                    r.consolidated = true
                RETURN count(r) as updated_count
                """
                
                result = await self.neo4j.execute_cypher(fallback_query, {
                    'original_type': original_type,
                    'canonical_type': mapping['canonical_type'],
                    'definition': mapping['definition'],
                    'session_id': session_id
                })
                
                count = result[0]['updated_count'] if result else 0
                logger.info(f"Updated {count} relationships with canonical_relationship_type property")
    
    def _get_predefined_entity_types(self) -> List[TypeDefinition]:
        """Get predefined entity types with definitions"""
        return [
            TypeDefinition(
                type_name="Person",
                definition="Individual human beings mentioned in interviews",
                frequency=0
            ),
            TypeDefinition(
                type_name="Organization", 
                definition="Companies, institutions, universities, or formal groups",
                frequency=0
            ),
            TypeDefinition(
                type_name="Tool",
                definition="Software applications, platforms, or technical tools",
                frequency=0
            ),
            TypeDefinition(
                type_name="Method",
                definition="Approaches, methodologies, practices, or processes",
                frequency=0
            )
        ]
    
    def _get_predefined_relationship_types(self) -> List[TypeDefinition]:
        """Get predefined relationship types with definitions"""
        return [
            TypeDefinition(
                type_name="WORKS_AT",
                definition="Employment or institutional affiliation relationship",
                frequency=0
            ),
            TypeDefinition(
                type_name="USES",
                definition="Utilizes, employs, or operates a tool, method, or technology",
                frequency=0
            ),
            TypeDefinition(
                type_name="ADVOCATES_FOR",
                definition="Supports, promotes, or champions something positively",
                frequency=0
            ),
            TypeDefinition(
                type_name="SKEPTICAL_OF",
                definition="Doubts, questions, or has concerns about something",
                frequency=0
            ),
            TypeDefinition(
                type_name="COLLABORATES_WITH",
                definition="Works together or partners with on projects or activities",
                frequency=0
            ),
            TypeDefinition(
                type_name="MANAGES",
                definition="Supervises, oversees, leads, or directs",
                frequency=0
            )
        ]
```

### Phase 3: Output Enhancement (Day 3)

#### 3.1 Enhanced Markdown Export
**File**: `qc/utils/markdown_exporter.py`

Update to include type definitions in output:

```python
# Add to existing export_analysis method
def export_analysis(self, entities: List[Dict], relationships: List[Dict], 
                   codes: List[Dict], filename: str = None, metadata: Dict = None) -> str:
    """Enhanced export with type definitions"""
    
    # ... existing logic unchanged until entity section
    
    def _generate_entities_section(self, entities: List[Dict]) -> str:
        """Enhanced entity section with type definitions"""
        
        # Group entities by type
        entities_by_type = defaultdict(list)
        type_definitions = {}
        
        for entity in entities:
            entity_type = entity.get('type', 'Unknown')
            entities_by_type[entity_type].append(entity)
            
            # Collect type definition
            if 'type_definition' in entity and entity['type_definition']:
                type_definitions[entity_type] = entity['type_definition']
        
        content = "## Entities by Type\n\n"
        
        for entity_type, type_entities in entities_by_type.items():
            count = len(type_entities)
            definition = type_definitions.get(entity_type, "No definition provided")
            
            content += f"### {entity_type} ({count})\n"
            content += f"**Definition**: {definition}\n\n"
            
            for entity in type_entities:
                content += f"#### {entity['name']}\n"
                
                # Add entity-specific details if available
                if entity.get('context'):
                    content += f"*Context*: {entity['context'][:100]}...\n"
                content += "\n"
        
        return content
    
    def _generate_relationships_section(self, relationships: List[Dict]) -> str:
        """Enhanced relationship section with type definitions"""
        
        # Group relationships by type
        relationships_by_type = defaultdict(list)
        type_definitions = {}
        
        for relationship in relationships:
            # Handle both direct type and canonical type properties
            rel_type = (relationship.get('canonical_relationship_type') or 
                       relationship.get('relationship_type') or 
                       relationship.get('type', 'RELATED_TO'))
            
            relationships_by_type[rel_type].append(relationship)
            
            # Collect type definition
            if 'relationship_definition' in relationship and relationship['relationship_definition']:
                type_definitions[rel_type] = relationship['relationship_definition']
        
        content = "## Relationship Network\n\n"
        
        for rel_type, type_relationships in relationships_by_type.items():
            count = len(type_relationships)
            definition = type_definitions.get(rel_type, "No definition provided")
            
            content += f"### {rel_type} ({count})\n"
            content += f"**Definition**: {definition}\n\n"
            
            for relationship in type_relationships:
                confidence = relationship.get('confidence', 0.0)
                context = relationship.get('context', '')
                
                content += f"- **{relationship['source_entity']}** → **{relationship['target_entity']}** "
                content += f"(confidence: {confidence:.2f})\n"
                
                if context:
                    content += f"  - Context: \"{context[:100]}{'...' if len(context) > 100 else ''}\"\n"
                
                # Show if this was consolidated
                if relationship.get('consolidated') and relationship.get('original_type'):
                    content += f"  - *Originally*: {relationship['original_type']}\n"
                
                content += "\n"
        
        return content
```

### Phase 4: Testing and Validation

#### 4.1 Unit Tests
**File**: `tests/test_llm_consolidator.py` (NEW)

```python
import pytest
from qc.consolidation.llm_consolidator import LLMConsolidator
from qc.consolidation.consolidation_schemas import ConsolidationRequest, TypeDefinition

class TestLLMConsolidator:
    """Test LLM consolidation functionality"""
    
    @pytest.fixture
    async def consolidator(self, mock_gemini_client):
        return LLMConsolidator(mock_gemini_client)
    
    async def test_basic_consolidation(self, consolidator):
        """Test basic type consolidation"""
        request = ConsolidationRequest(
            entity_types=[
                TypeDefinition(type_name="API Gateway", definition="Manages API requests", frequency=3),
                TypeDefinition(type_name="Service Mesh", definition="Handles microservice communication", frequency=2),
                TypeDefinition(type_name="Load Balancer", definition="Distributes traffic", frequency=1)
            ],
            relationship_types=[
                TypeDefinition(type_name="depends_on", definition="Requires for functionality", frequency=5),
                TypeDefinition(type_name="relies_on", definition="Needs for operation", frequency=3)
            ],
            validation_mode="open"
        )
        
        response = await consolidator.consolidate_session_types(request)
        
        assert len(response.consolidated_entities) > 0
        assert len(response.consolidated_relationships) > 0
        assert response.summary
    
    async def test_hybrid_mode_prefers_predefined(self, consolidator):
        """Test that hybrid mode prefers predefined types"""
        # Implementation test for predefined type preference
        pass
    
    async def test_fallback_on_llm_failure(self, consolidator):
        """Test fallback behavior when LLM fails"""
        # Implementation test for error handling
        pass
```

#### 4.2 Integration Tests
**File**: `tests/test_consolidation_integration.py` (NEW)

```python
async def test_end_to_end_consolidation(cli_instance, sample_interviews):
    """Test complete consolidation workflow"""
    
    # Clear database
    await cli_instance.neo4j.clear_database()
    
    # Run analysis with consolidation
    output_path = await cli_instance.analyze_interviews(
        files=list(sample_interviews.values()),
        validation_mode="hybrid",
        enable_validation=True
    )
    
    # Verify consolidation occurred
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        content = f.read()
        
        # Check for type definitions in output
        assert "**Definition**:" in content
        assert "No definition provided" not in content
        
        # Check for consolidated types
        assert "Originally:" in content  # Shows consolidation happened
```

## Implementation Guidelines

### Development Phases
1. **Phase 1** (Days 1-2): Schema and infrastructure setup
2. **Phase 2** (Day 2): CLI integration and consolidation logic  
3. **Phase 3** (Day 3): Output enhancement and testing
4. **Phase 4** (Day 3): Testing and validation

### Testing Strategy
- Unit tests for consolidation logic
- Integration tests for end-to-end workflow
- Manual testing with real interview data
- Performance testing for consolidation LLM calls

### Error Handling
- LLM consolidation failures → fallback to original types with basic definitions
- Neo4j update failures → log errors but continue with export
- Invalid consolidation responses → validation and retry logic

### Performance Considerations
- Consolidation happens once per session (not per entity)
- Batch Neo4j updates for efficiency
- Cache consolidation results for similar type sets
- Implement timeout handling for LLM calls

## Rollback Plan

If consolidation causes issues:
1. **Disable consolidation**: Add `--no-consolidation` CLI flag
2. **Data recovery**: Clear consolidated flags in Neo4j
3. **Fallback mode**: Use existing string-based consolidation
4. **Schema rollback**: Remove definition fields if necessary

## Success Metrics

### Functional Metrics
- Type definitions present in 100% of outputs
- Semantically appropriate consolidations (manual review)
- No regression in extraction accuracy
- Performance impact <20% increase in processing time

### Quality Metrics  
- Clear, understandable type definitions
- Logical relationship directions (e.g., Person WORKS_AT Organization)
- Appropriate consolidation granularity (not over/under-consolidated)
- Consistent behavior across validation modes

## Future Enhancements

### Phase 2 Potential Features
- User-reviewable consolidation suggestions
- Consolidation confidence thresholds
- Custom type definition templates
- Cross-session type learning and reuse
- Advanced semantic similarity algorithms

This plan provides a comprehensive, methodical approach to implementing LLM-powered type consolidation while minimizing risk to the existing working system.