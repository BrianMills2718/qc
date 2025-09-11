"""
Pydantic schemas for LLM-powered type consolidation
"""

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