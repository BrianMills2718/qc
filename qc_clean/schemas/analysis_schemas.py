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
    example_quotes: List[str] = Field(default_factory=list, description="1-3 illustrative quotes")
    mention_count: int = Field(..., description="Approximate number of times this theme is mentioned or referenced in the interviews")
    discovery_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0 using the FULL range: 0.0-0.3 weak, 0.3-0.6 moderate, 0.6-0.8 strong, 0.8-1.0 very strong")
    reasoning: str = Field(
        default="",
        description="Brief explanation of why this code was created and what analytical decision led to it",
    )


class CodeHierarchy(BaseModel):
    """Complete hierarchical code structure from Phase 1 analysis"""
    codes: List[ThematicCode] = Field(default_factory=list, description="Complete hierarchical code structure")
    total_codes: int = Field(..., description="Total number of codes identified")
    analysis_confidence: float = Field(..., description="Overall analysis confidence")
    analytical_memo: str = Field(
        default="",
        description="Analytical memo: record your reasoning, uncertainties, and emerging patterns",
    )


class ParticipantProfile(BaseModel):
    """Individual participant analysis"""
    name: str = Field(..., description="Participant name or identifier")
    role: str = Field(..., description="Professional role or position")
    characteristics: List[str] = Field(default_factory=list, description="Key characteristics noted")
    perspective_summary: str = Field(..., description="Summary of their viewpoint")
    codes_emphasized: List[str] = Field(default_factory=list, description="Top 5-7 code IDs this participant emphasized MOST (not all codes, only the strongest)")


class SpeakerAnalysis(BaseModel):
    """Speaker and participant analysis from Phase 2"""
    participants: List[ParticipantProfile] = Field(default_factory=list, description="Identified participants")
    consensus_themes: List[str] = Field(default_factory=list, description="For multiple speakers: areas of agreement. For single speaker: the speaker's strongest/most consistent positions")
    divergent_viewpoints: List[str] = Field(default_factory=list, description="For multiple speakers: areas of disagreement. For single speaker: internal tensions, ambivalences, or contradictions in the speaker's views")
    perspective_mapping: Dict[str, List[str]] = Field(default_factory=dict, description="Participant name to their top 5-7 most emphasized code IDs")
    analytical_memo: str = Field(
        default="",
        description="Analytical memo: record your reasoning, uncertainties, and emerging patterns",
    )


class EntityRelationship(BaseModel):
    """Relationship between entities"""
    entity_1: str = Field(..., description="First entity in relationship")
    entity_2: str = Field(..., description="Second entity in relationship")
    relationship_type: str = Field(..., description="Type of relationship")
    strength: float = Field(..., ge=0.0, le=1.0, description="Relationship strength")
    supporting_evidence: List[str] = Field(default_factory=list, description="Supporting quotes/evidence")


class EntityMapping(BaseModel):
    """Entity and relationship mapping from Phase 3"""
    entities: List[str] = Field(default_factory=list, description="Key entities identified")
    relationships: List[EntityRelationship] = Field(default_factory=list, description="Entity relationships")
    cause_effect_chains: List[str] = Field(default_factory=list, description="Identified causal relationships")
    conceptual_connections: List[str] = Field(default_factory=list, description="Cross-cutting connections")
    analytical_memo: str = Field(
        default="",
        description="Analytical memo: record your reasoning, uncertainties, and emerging patterns",
    )


class AnalysisRecommendation(BaseModel):
    """Individual recommendation from analysis"""
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation")
    priority: str = Field(..., description="Priority level: high, medium, low")
    supporting_themes: List[str] = Field(default_factory=list, description="Themes supporting this recommendation")


class ConfidenceEntry(BaseModel):
    """Confidence assessment for a theme"""
    level: str = Field(..., description="Confidence level: high, medium, low")
    score: float = Field(..., ge=0.0, le=1.0, description="Numeric confidence score")
    evidence: str = Field("", description="Supporting evidence for this confidence level")


class AnalysisSynthesis(BaseModel):
    """Final synthesis and recommendations from Phase 4"""
    executive_summary: str = Field(..., description="Comprehensive summary")
    key_findings: List[str] = Field(default_factory=list, description="Major findings with evidence")
    cross_cutting_patterns: List[str] = Field(default_factory=list, description="Patterns across themes")
    actionable_recommendations: List[AnalysisRecommendation] = Field(default_factory=list, description="Specific recommendations")
    confidence_assessment: Dict[str, Any] = Field(default_factory=dict, description="Confidence levels by theme, each with level/score/evidence")
    analytical_memo: str = Field(
        default="",
        description="Analytical memo: record your reasoning, uncertainties, and emerging patterns",
    )