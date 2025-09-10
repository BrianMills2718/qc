"""
LLM-powered semantic type consolidation service
"""

import logging
from typing import List, Dict, Any
from ..core.native_gemini_client import NativeGeminiClient
from .consolidation_schemas import ConsolidationRequest, ConsolidationResponse, ConsolidatedType, TypeDefinition

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
        
        logger.info(f"Starting LLM consolidation for {len(request.entity_types)} entity types and {len(request.relationship_types)} relationship types")
        
        # Call Gemini with structured output
        try:
            response = self.client.structured_output(
                prompt=prompt,
                schema=ConsolidationResponse
            )
            
            # Extract the response data
            consolidation_data = response['response']
            consolidation_response = ConsolidationResponse(**consolidation_data)
            
            logger.info(f"Consolidated {len(request.entity_types)} entity types into "
                       f"{len(consolidation_response.consolidated_entities)} canonical types")
            logger.info(f"Consolidated {len(request.relationship_types)} relationship types into "
                       f"{len(consolidation_response.consolidated_relationships)} canonical types")
            
            return consolidation_response
            
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
6. CRITICAL: Handle inverse relationships by consolidating them with their canonical counterpart:
   - "employs" → "WORKS_AT" (Organization employs Person = Person WORKS_AT Organization)
   - "employed_by" → "WORKS_AT" (Person employed_by Organization = Person WORKS_AT Organization)
   - "owns" → "OWNS" (consolidate with standard directional form)
   - "owned_by" → "OWNS" (reverse direction will be handled during processing)

EXAMPLES OF REQUIRED CONSOLIDATIONS:
- Input: ["works_at", "employs"] → Output: Both consolidated into "WORKS_AT" 
- Input: ["uses", "used_by"] → Output: Both consolidated into "USES"
- Input: ["collaborates_with", "partners_with"] → Output: Both consolidated into "COLLABORATES_WITH"

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