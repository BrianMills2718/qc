"""
Pydantic schemas for structured qualitative coding analysis output.
These schemas define the exact structure expected from LLM-based analysis phases.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ThematicCode(BaseModel):
    """Individual thematic code in hierarchical structure"""
    id: str = Field(..., description="Unique ID in CAPS_WITH_UNDERSCORES format")
    name: str = Field(..., description="Human-readable code name")
    description: str = Field(..., description="2-3 sentence detailed description")
    semantic_definition: str = Field(..., description="Clear definition of what qualifies")
    parent_id: Optional[str] = Field(None, description="ID of parent code, null for top-level")
    level: int = Field(..., description="Hierarchy level (0=top, 1=sub, 2=detailed)")
    example_quotes: List[str] = Field(..., description="1-3 illustrative quotes")
    discovery_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class CodeHierarchy(BaseModel):
    """Complete hierarchical code structure from Phase 1 analysis"""
    codes: List[ThematicCode] = Field(..., description="Complete hierarchical code structure")
    total_codes: int = Field(..., description="Total number of codes identified")
    analysis_confidence: float = Field(..., description="Overall analysis confidence")


class ParticipantProfile(BaseModel):
    """Individual participant analysis"""
    name: str = Field(..., description="Participant name or identifier")
    role: str = Field(..., description="Professional role or position")
    characteristics: List[str] = Field(..., description="Key characteristics noted")
    perspective_summary: str = Field(..., description="Summary of their viewpoint")
    codes_emphasized: List[str] = Field(..., description="Codes this participant emphasized")


class SpeakerAnalysis(BaseModel):
    """Speaker and participant analysis from Phase 2"""
    participants: List[ParticipantProfile] = Field(..., description="Identified participants")
    consensus_themes: List[str] = Field(..., description="Areas of agreement")
    divergent_viewpoints: List[str] = Field(..., description="Areas of disagreement")
    perspective_mapping: Dict[str, List[str]] = Field(..., description="Participant to codes mapping")


class EntityRelationship(BaseModel):
    """Relationship between entities"""
    entity_1: str = Field(..., description="First entity in relationship")
    entity_2: str = Field(..., description="Second entity in relationship")
    relationship_type: str = Field(..., description="Type of relationship")
    strength: float = Field(..., ge=0.0, le=1.0, description="Relationship strength")
    supporting_evidence: List[str] = Field(..., description="Supporting quotes/evidence")


class EntityMapping(BaseModel):
    """Entity and relationship mapping from Phase 3"""
    entities: List[str] = Field(..., description="Key entities identified")
    relationships: List[EntityRelationship] = Field(..., description="Entity relationships")
    cause_effect_chains: List[str] = Field(..., description="Identified causal relationships")
    conceptual_connections: List[str] = Field(..., description="Cross-cutting connections")


class AnalysisRecommendation(BaseModel):
    """Individual recommendation from analysis"""
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation")
    priority: str = Field(..., description="Priority level: high, medium, low")
    supporting_themes: List[str] = Field(..., description="Themes supporting this recommendation")


class AnalysisSynthesis(BaseModel):
    """Final synthesis and recommendations from Phase 4"""
    executive_summary: str = Field(..., description="Comprehensive summary")
    key_findings: List[str] = Field(..., description="Major findings with evidence")
    cross_cutting_patterns: List[str] = Field(..., description="Patterns across themes")
    actionable_recommendations: List[AnalysisRecommendation] = Field(..., description="Specific recommendations")
    confidence_assessment: Dict[str, float] = Field(..., description="Confidence levels by theme")