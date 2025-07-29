"""
Pydantic models for LLM-native global analysis approach.

These models represent the comprehensive analysis of all 103 interviews
processed simultaneously using Gemini's 1M token context window.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
from enum import Enum


class QuoteEvidence(BaseModel):
    """A single quote from an interview with full traceability."""
    quote_id: str = Field(description="Unique quote identifier (e.g., Q_001_045)")
    interview_id: str = Field(description="Interview identifier (e.g., INT_001)")
    interview_name: str = Field(description="Original file name")
    text: str = Field(description="Exact quote text")
    line_number: int = Field(description="Approximate line number in interview")
    context: str = Field(description="Brief context around the quote")
    speaker_role: Optional[str] = Field(description="Role/position of speaker if identifiable")


class GlobalCode(BaseModel):
    """Code identified across entire dataset with global context."""
    code_id: str = Field(description="Unique code identifier (e.g., CODE_001)")
    name: str = Field(description="Descriptive code name")
    definition: str = Field(description="What this code represents")
    frequency: int = Field(description="Total occurrences across all interviews")
    interviews_present: List[str] = Field(description="Interview IDs where this code appears")
    key_quotes: List[QuoteEvidence] = Field(description="Most representative quotes (3-5)")
    first_appearance: str = Field(description="Interview ID where first mentioned")
    evolution_notes: str = Field(description="How this code developed across dataset")
    saturation_point: Optional[str] = Field(description="Interview where code stabilized")
    theme_id: Optional[str] = Field(description="ID of the theme this code belongs to")
    parent_code_id: Optional[str] = Field(default=None, description="Parent code ID if this is a sub-code")
    hierarchy_level: int = Field(default=0, description="0=top-level, 1=sub-code, 2=sub-sub-code")
    child_codes: List[str] = Field(default_factory=list, description="List of child code IDs")


class CodeCategory(BaseModel):
    """Category grouping related codes."""
    category_id: str = Field(description="Unique category identifier")
    name: str = Field(description="Category name")
    description: str = Field(description="What this category represents")
    codes: List[str] = Field(description="Code IDs that belong to this category")
    prevalence: float = Field(description="Proportion of interviews with this category (0.0-1.0)")


class QuoteChain(BaseModel):
    """Sequence of quotes showing progression of an idea."""
    chain_id: str = Field(description="Unique chain identifier")
    theme_id: str = Field(description="Related theme ID")
    chain_type: Literal["evolution", "contradiction", "consensus_building", "problem_solution"] = Field(
        description="Type of progression this chain represents"
    )
    description: str = Field(description="What this chain demonstrates")
    quotes_sequence: List[QuoteEvidence] = Field(
        description="Ordered sequence of quotes showing progression"
    )
    key_transition_points: List[str] = Field(
        description="Interview IDs where major shifts occurred"
    )
    interpretation: str = Field(description="Analysis of what this chain reveals")


class StakeholderPosition(BaseModel):
    """Position of a stakeholder group on a theme."""
    stakeholder_type: str = Field(description="Type of stakeholder (e.g., researcher, practitioner)")
    position: Literal["strongly_support", "support", "neutral", "oppose", "strongly_oppose"] = Field(
        description="Position on the theme"
    )
    evidence_quotes: List[QuoteEvidence] = Field(description="Quotes supporting this position")
    frequency: int = Field(description="Number of stakeholders with this position")
    key_arguments: List[str] = Field(description="Main arguments for this position")


class ContradictionPair(BaseModel):
    """Opposing viewpoints on the same issue."""
    contradiction_id: str = Field(description="Unique identifier")
    theme_id: str = Field(description="Related theme")
    issue: str = Field(description="The contested issue")
    position_a: str = Field(description="First position")
    position_b: str = Field(description="Opposing position")
    evidence_a: List[QuoteEvidence] = Field(description="Evidence for position A")
    evidence_b: List[QuoteEvidence] = Field(description="Evidence for position B")
    stakeholders_a: List[str] = Field(description="Who holds position A")
    stakeholders_b: List[str] = Field(description="Who holds position B")
    resolution_attempts: Optional[List[QuoteEvidence]] = Field(
        description="Quotes attempting to reconcile positions"
    )


class CrossInterviewTheme(BaseModel):
    """Theme that spans multiple interviews with full evidence."""
    theme_id: str = Field(description="Unique theme identifier")
    name: str = Field(description="Theme name")
    description: str = Field(description="What this theme represents")
    categories: List[CodeCategory] = Field(description="Categories within this theme")
    codes: List[str] = Field(description="All code IDs in this theme")
    prevalence: float = Field(description="Proportion of interviews containing theme (0.0-1.0)")
    interviews_count: int = Field(description="Number of interviews with this theme")
    
    # Evidence and progression
    quote_chains: List[str] = Field(description="Quote chain IDs showing theme development")
    key_quotes: List[QuoteEvidence] = Field(description="Most representative quotes")
    
    # Stakeholder analysis
    stakeholder_positions: List[StakeholderPosition] = Field(
        description="Different stakeholder positions on this theme"
    )
    contradictions: List[str] = Field(description="Contradiction IDs within this theme")
    
    # Theoretical development
    theoretical_memo: str = Field(description="Analytical memo about this theme")
    policy_implications: Optional[str] = Field(description="Policy relevance if applicable")
    confidence_score: float = Field(description="Confidence in theme identification (0.0-1.0)")


class TheoricalSaturationAssessment(BaseModel):
    """Assessment of when theoretical saturation occurred."""
    saturation_point: str = Field(description="Interview ID where saturation reached")
    interview_number: int = Field(description="Sequential number of that interview")
    evidence: str = Field(description="Why saturation occurred at this point")
    new_codes_curve: List[int] = Field(
        description="New codes found in each batch of 10 interviews"
    )
    new_themes_curve: List[int] = Field(
        description="New themes found in each batch of 10 interviews"
    )
    stabilization_indicators: List[str] = Field(
        description="Signs that theory stabilized"
    )
    post_saturation_validation: str = Field(
        description="What remaining interviews confirmed"
    )


class CodeProgression(BaseModel):
    """How a code evolved throughout the dataset."""
    code_id: str = Field(description="Code being tracked")
    progression_type: Literal["emerging", "evolving", "stable", "declining"] = Field(
        description="Pattern of code development"
    )
    timeline: List[Dict[str, Any]] = Field(
        description="Interview batches with frequency and definition changes"
    )
    definition_evolution: List[str] = Field(
        description="How the code's meaning evolved"
    )
    peak_period: str = Field(description="Interview range where code was most prevalent")
    key_contributors: List[str] = Field(description="Interviews that shaped this code")


class ContradictionPair(BaseModel):
    """A pair of contradicting viewpoints on the same topic."""
    contradiction_id: str = Field(description="Unique identifier (e.g., CONT_001)")
    topic: str = Field(description="The topic/issue where contradiction exists")
    position_1: str = Field(description="First position/viewpoint")
    position_1_holders: List[str] = Field(description="Who holds position 1 (names/roles)")
    position_1_quotes: List[QuoteEvidence] = Field(description="Supporting quotes for position 1")
    position_2: str = Field(description="Opposing position/viewpoint")
    position_2_holders: List[str] = Field(description="Who holds position 2 (names/roles)")
    position_2_quotes: List[QuoteEvidence] = Field(description="Supporting quotes for position 2")
    resolution_suggested: Optional[str] = Field(description="Any suggested resolution or middle ground")
    theme_ids: List[str] = Field(description="Related theme IDs")
    code_ids: List[str] = Field(description="Related code IDs")


class StakeholderPosition(BaseModel):
    """A stakeholder's position on key issues."""
    stakeholder_id: str = Field(description="Unique identifier")
    stakeholder_name: str = Field(description="Name of person/group")
    stakeholder_type: str = Field(description="Type: researcher, management, client, etc.")
    position_summary: str = Field(description="Overall position/stance")
    supporting_quotes: List[QuoteEvidence] = Field(description="Quotes supporting their position")
    concerns: List[str] = Field(description="Main concerns expressed")
    recommendations: List[str] = Field(description="Their recommendations")
    influence_level: Literal["high", "medium", "low"] = Field(description="Perceived influence level")


class GlobalCodingResult(BaseModel):
    """Complete result from global analysis of all 103 interviews."""
    # Metadata
    study_id: str = Field(description="Unique identifier for this analysis")
    analysis_timestamp: datetime = Field(description="When analysis was performed")
    research_question: str = Field(description="Guiding research question")
    interviews_analyzed: int = Field(description="Total interviews processed (should be 103)")
    total_tokens_analyzed: int = Field(description="Token count of entire dataset")
    
    # Core findings
    themes: List[CrossInterviewTheme] = Field(description="Major themes across dataset")
    codes: List[GlobalCode] = Field(description="All codes with global context")
    categories: List[CodeCategory] = Field(description="Code categories")
    
    # Progressions and chains
    quote_chains: List[QuoteChain] = Field(description="Sequences showing idea development")
    code_progressions: List[CodeProgression] = Field(description="How codes evolved")
    
    # Contradictions and positions
    contradictions: List[ContradictionPair] = Field(description="Opposing viewpoints found")
    stakeholder_mapping: Dict[str, List[str]] = Field(
        description="Stakeholder type to theme positions"
    )
    
    # Theoretical insights
    saturation_assessment: TheoricalSaturationAssessment = Field(
        description="When saturation occurred"
    )
    theoretical_insights: List[str] = Field(description="Key theoretical discoveries")
    emergent_theory: str = Field(description="Main theoretical contribution")
    methodological_notes: str = Field(description="Notes on analysis process")
    
    # Quality metrics
    processing_metadata: Dict[str, Any] = Field(
        description="Processing time, token usage, etc."
    )
    confidence_scores: Dict[str, float] = Field(
        description="Confidence in different aspects of analysis"
    )


class CSVExportData(BaseModel):
    """Data formatted for CSV export with full traceability."""
    themes_table: List[Dict[str, Any]] = Field(
        description="Main themes with prevalence and confidence"
    )
    codes_table: List[Dict[str, Any]] = Field(
        description="All codes with frequencies and definitions"
    )
    quotes_table: List[Dict[str, Any]] = Field(
        description="All quotes with theme/code mappings"
    )
    quote_chains_table: List[Dict[str, Any]] = Field(
        description="Quote chains showing progressions"
    )
    contradictions_table: List[Dict[str, Any]] = Field(
        description="Contradictions with evidence"
    )
    stakeholder_positions_table: List[Dict[str, Any]] = Field(
        description="Stakeholder positions on themes"
    )
    saturation_curve_table: List[Dict[str, Any]] = Field(
        description="Saturation metrics by interview batch"
    )
    traceability_matrix: List[Dict[str, Any]] = Field(
        description="Complete theme->code->quote->interview mapping"
    )


class EnhancedResult(BaseModel):
    """Enhanced result with full traceability from second LLM call."""
    global_analysis: GlobalCodingResult = Field(description="Original global analysis")
    
    # Enhanced outputs
    csv_export_data: CSVExportData = Field(description="Data formatted for CSV export")
    markdown_report: str = Field(description="Complete markdown report with all findings")
    executive_summary: str = Field(description="One-page executive summary")
    
    # Additional traceability
    complete_quote_inventory: List[QuoteEvidence] = Field(
        description="All significant quotes with full metadata"
    )
    interview_summaries: Dict[str, str] = Field(
        description="Brief summary of each interview's contribution"
    )
    
    # Quality metrics
    traceability_completeness: float = Field(
        description="Percentage of findings with full traceability (0.0-1.0)"
    )
    quote_chain_coverage: float = Field(
        description="Percentage of themes with quote chains (0.0-1.0)"
    )
    stakeholder_coverage: float = Field(
        description="Percentage of participants mapped to positions (0.0-1.0)"
    )
    evidence_strength: float = Field(
        description="Overall strength of evidence for findings (0.0-1.0)"
    )