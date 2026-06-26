"""
Pydantic schemas for structured qualitative coding analysis output.
These schemas define the exact structure expected from LLM-based analysis phases.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

from qc_clean.schemas.validators import Confidence01


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
    discovery_confidence: Confidence01 = Field(..., description="Confidence score from 0.0 to 1.0 using the FULL range: 0.0-0.3 weak, 0.3-0.6 moderate, 0.6-0.8 strong, 0.8-1.0 very strong")
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


class SegmentDecision(BaseModel):
    """Exhaustive coding: the code decision for one segment of the corpus."""
    segment_index: int = Field(..., description="0-based index of the segment (as numbered in the prompt)")
    code_ids: List[str] = Field(default_factory=list, description="IDs of codes that apply to this segment; EMPTY means no code applies (examined, not relevant)")


class ExhaustiveCodingResponse(BaseModel):
    """Discover a codebook AND render a decision for every segment in one call."""
    codes: List[ThematicCode] = Field(default_factory=list, description="The hierarchical codebook discovered across the corpus")
    decisions: List[SegmentDecision] = Field(default_factory=list, description="One decision per segment — EVERY segment index must appear exactly once")
    total_codes: int = Field(default=0, description="Total number of codes")
    analysis_confidence: float = Field(default=0.0, description="Overall analysis confidence")
    analytical_memo: str = Field(default="", description="Analytical memo: reasoning, uncertainties, emerging patterns")


class ParticipantProfile(BaseModel):
    """Individual participant analysis"""
    name: str = Field(..., description="Participant name or identifier")
    role: str = Field(..., description="Professional role or position")
    characteristics: List[str] = Field(default_factory=list, description="Key characteristics noted")
    perspective_summary: str = Field(..., description="Summary of their viewpoint")
    position_statements: List[str] = Field(
        default_factory=list,
        description="2-5 bounded position statements that capture what this participant is asserting, valuing, contesting, or evaluating",
    )
    codes_emphasized: List[str] = Field(default_factory=list, description="Top 5-7 code IDs this participant emphasized MOST (not all codes, only the strongest)")


class PerspectiveMapEntry(BaseModel):
    """Maps a participant to their most emphasized codes."""
    participant_name: str = Field(..., description="Name of the participant")
    code_ids: List[str] = Field(default_factory=list, description="Top 5-7 most emphasized code IDs")


class SpeakerAnalysis(BaseModel):
    """Speaker and participant analysis from Phase 2"""
    participants: List[ParticipantProfile] = Field(default_factory=list, description="Identified participants")
    consensus_themes: List[str] = Field(default_factory=list, description="For multiple speakers: areas of agreement. For single speaker: the speaker's strongest/most consistent positions")
    divergent_viewpoints: List[str] = Field(default_factory=list, description="For multiple speakers: areas of disagreement. For single speaker: internal tensions, ambivalences, or contradictions in the speaker's views")
    perspective_mapping: List[PerspectiveMapEntry] = Field(default_factory=list, description="Each participant mapped to their top 5-7 most emphasized code IDs")
    analytical_memo: str = Field(
        default="",
        description="Analytical memo: record your reasoning, uncertainties, and emerging patterns",
    )


class EntityRelationship(BaseModel):
    """Relationship between entities"""
    entity_1: str = Field(..., description="First entity in relationship")
    entity_2: str = Field(..., description="Second entity in relationship")
    relationship_type: str = Field(..., description="Type of relationship")
    strength: Confidence01 = Field(..., description="Relationship strength")
    supporting_evidence: List[str] = Field(default_factory=list, description="Supporting quotes/evidence")


class CodeRelationshipCandidate(BaseModel):
    """Relationship between two thematic codes."""
    source_code: str = Field(
        ...,
        description="Exact code ID or code name for the source code",
    )
    target_code: str = Field(
        ...,
        description="Exact code ID or code name for the target code",
    )
    relationship_type: str = Field(..., description="Type of analytic relationship")
    strength: Confidence01 = Field(..., description="Relationship strength")
    supporting_evidence: List[str] = Field(default_factory=list, description="Supporting quotes/evidence")
    conditions: List[str] = Field(default_factory=list, description="Conditions shaping the relationship")
    consequences: List[str] = Field(default_factory=list, description="Consequences or implications of the relationship")


class EntityMapping(BaseModel):
    """Entity and relationship mapping from Phase 3"""
    entities: List[str] = Field(default_factory=list, description="Key entities identified")
    relationships: List[EntityRelationship] = Field(default_factory=list, description="Entity relationships")
    code_relationships: List[CodeRelationshipCandidate] = Field(
        default_factory=list,
        description="Analytic relationships between thematic codes",
    )
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
    score: Confidence01 = Field(..., description="Numeric confidence score")
    evidence: str = Field("", description="Supporting evidence for this confidence level")


class ThemeConfidence(BaseModel):
    """Confidence assessment for a specific theme."""
    theme: str = Field(..., description="Theme name or code ID")
    level: str = Field(..., description="Confidence level: high, medium, low")
    score: Confidence01 = Field(..., description="Numeric confidence score")
    evidence: str = Field(default="", description="Supporting evidence for this confidence level")


class AnalysisSynthesis(BaseModel):
    """Final synthesis and recommendations from Phase 4"""
    executive_summary: str = Field(..., description="Comprehensive summary")
    key_findings: List[str] = Field(default_factory=list, description="Major findings with evidence")
    cross_cutting_patterns: List[str] = Field(default_factory=list, description="Patterns across themes")
    actionable_recommendations: List[AnalysisRecommendation] = Field(default_factory=list, description="Specific recommendations")
    confidence_assessment: List[ThemeConfidence] = Field(default_factory=list, description="Confidence level for each theme")
    analytical_memo: str = Field(
        default="",
        description="Analytical memo: record your reasoning, uncertainties, and emerging patterns",
    )


class AbductiveCandidateExplanationItem(BaseModel):
    """One provisional explanation candidate for observed descriptive patterns."""
    source_pattern_ids: List[str] = Field(
        ...,
        description="ObservedPattern IDs this candidate explains; every ID must come from the prompt",
    )
    explanation_text: str = Field(
        ...,
        description="Plain-language provisional explanation of the observed pattern",
    )
    mechanism_summary: str = Field(
        ...,
        description="Concise mechanism/process that would make the explanation plausible",
    )
    rival_explanations: List[str] = Field(
        default_factory=list,
        description="Alternative explanations that could account for the same observed pattern",
    )
    observable_implications: List[str] = Field(
        default_factory=list,
        description="Observable traces or data patterns expected if this explanation is right",
    )
    evidence_gaps: List[str] = Field(
        default_factory=list,
        description="Missing evidence needed before upgrading this candidate",
    )
    confidence: Confidence01 = Field(
        default=0.5,
        description="Provisional confidence only; not calibrated probability or validation evidence",
    )


class AbductiveCandidateExplanationResponse(BaseModel):
    """Structured abductive candidate explanation response."""
    candidates: List[AbductiveCandidateExplanationItem] = Field(
        default_factory=list,
        description="Provisional candidate explanations for observed patterns",
    )
    analytical_memo: str = Field(
        default="",
        description="Methodological memo noting uncertainty, rivalry, and evidence gaps",
    )
