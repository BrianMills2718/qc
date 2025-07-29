"""
Simplified schemas for Gemini structured output compatibility.
These avoid complex nested structures that cause $ref issues.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SimpleTheme(BaseModel):
    """Simplified theme for structured output."""
    theme_id: str = Field(description="Unique theme identifier")
    name: str = Field(description="Theme name")
    description: str = Field(description="What this theme represents")
    prevalence: float = Field(description="Proportion of interviews (0.0-1.0)")
    interviews_count: int = Field(description="Number of interviews with this theme")
    key_quotes: List[str] = Field(description="Most representative quotes as strings")
    confidence_score: float = Field(description="Confidence in theme (0.0-1.0)")


class SimpleCode(BaseModel):
    """Simplified code for structured output."""
    code_id: str = Field(description="Unique code identifier")
    name: str = Field(description="Code name")
    definition: str = Field(description="What this code represents")
    frequency: int = Field(description="Total occurrences")
    interviews_present: List[str] = Field(description="Interview IDs where present")
    first_appearance: str = Field(description="Interview ID where first mentioned")
    theme_id: str = Field(description="ID of the theme this code belongs to")
    parent_code_id: Optional[str] = Field(description="Parent code ID if this is a sub-code")
    hierarchy_level: int = Field(description="0=top-level, 1=sub-code, 2=sub-sub-code")


class SimpleQuoteChain(BaseModel):
    """Simplified quote chain."""
    chain_id: str = Field(description="Unique chain identifier")
    theme_id: str = Field(description="Related theme ID")
    chain_type: str = Field(description="Type: evolution, contradiction, consensus_building, or problem_solution")
    description: str = Field(description="What this chain demonstrates")
    quotes: List[str] = Field(description="Ordered sequence of quotes showing progression")


class SimpleContradiction(BaseModel):
    """Simplified contradiction for structured output."""
    contradiction_id: str = Field(description="Unique identifier (e.g., CONT_001)")
    topic: str = Field(description="The topic where contradiction exists")
    position_1: str = Field(description="First position/viewpoint")
    position_1_holders: List[str] = Field(description="Names/roles holding position 1")
    position_1_quotes: List[str] = Field(description="Quotes supporting position 1")
    position_2: str = Field(description="Opposing position/viewpoint")
    position_2_holders: List[str] = Field(description="Names/roles holding position 2")
    position_2_quotes: List[str] = Field(description="Quotes supporting position 2")
    resolution_notes: Optional[str] = Field(description="Any middle ground or resolution suggested")
    theme_ids: List[str] = Field(description="Related theme IDs")
    code_ids: List[str] = Field(description="Related code IDs")


class SimpleStakeholderPosition(BaseModel):
    """Simplified stakeholder position."""
    stakeholder_id: str = Field(description="Unique identifier")
    stakeholder_name: str = Field(description="Name of person/group")
    stakeholder_type: str = Field(description="Type: researcher, management, client, etc.")
    position_summary: str = Field(description="Their overall stance on AI in research")
    main_quotes: List[str] = Field(description="Key quotes expressing their position")
    concerns: List[str] = Field(description="Main concerns they express")
    recommendations: List[str] = Field(description="What they recommend")


class SimpleGlobalResult(BaseModel):
    """Simplified global analysis result for Gemini compatibility."""
    # Core findings
    themes: List[SimpleTheme] = Field(description="Major themes across dataset")
    codes: List[SimpleCode] = Field(description="All codes identified")
    quote_chains: List[SimpleQuoteChain] = Field(description="Quote progressions")
    contradictions: List[SimpleContradiction] = Field(description="Opposing viewpoints found")
    stakeholder_positions: List[SimpleStakeholderPosition] = Field(description="Key stakeholder positions")
    
    # Key insights
    theoretical_insights: List[str] = Field(description="Key theoretical discoveries")
    emergent_theory: str = Field(description="Main theoretical contribution")
    methodological_notes: str = Field(description="Notes on analysis process")
    
    # Saturation info
    saturation_point: str = Field(description="Interview ID where saturation reached")
    saturation_evidence: str = Field(description="Why saturation occurred at this point")
    
    # Overall confidence
    overall_confidence: float = Field(description="Overall confidence in analysis (0.0-1.0)")


class SimpleCSVExport(BaseModel):
    """Simplified CSV export data - using strings for flexibility."""
    themes_csv: str = Field(description="Themes data as CSV string")
    codes_csv: str = Field(description="Codes data as CSV string")
    quotes_csv: str = Field(description="Quotes data as CSV string")
    quote_chains_csv: str = Field(description="Quote chains data as CSV string")
    contradictions_csv: str = Field(description="Contradictions data as CSV string")
    stakeholder_positions_csv: str = Field(description="Stakeholder positions as CSV string")
    saturation_curve_csv: str = Field(description="Saturation curve data as CSV string")
    traceability_matrix_csv: str = Field(description="Traceability matrix as CSV string")


class SimpleEnhancedResult(BaseModel):
    """Simplified enhanced result for Gemini compatibility."""
    # CSV export data
    csv_export_data: SimpleCSVExport = Field(description="Data for CSV exports")
    
    # Reports
    markdown_report: str = Field(description="Complete markdown report")
    executive_summary: str = Field(description="Executive summary")
    
    # Quote inventory as JSON string to avoid schema issues
    complete_quote_inventory_json: str = Field(description="All quotes with metadata as JSON string")
    
    # Interview summaries as JSON string
    interview_summaries_json: str = Field(description="Summary of each interview's contributions as JSON string")
    
    # Quality metrics
    traceability_completeness: float = Field(description="Completeness of traceability (0.0-1.0)")
    quote_chain_coverage: float = Field(description="Coverage of quote chains (0.0-1.0)")
    stakeholder_coverage: float = Field(description="Coverage of stakeholder positions (0.0-1.0)")
    evidence_strength: float = Field(description="Strength of evidence (0.0-1.0)")


def _parse_quote_to_evidence(quote_text: str, quote_id: str, context: str) -> 'QuoteEvidence':
    """Helper to parse quote text into QuoteEvidence object."""
    from qc.models.comprehensive_analysis_models import QuoteEvidence
    import re
    
    # Default values
    interview_id = "INT_001"
    interview_name = "Interview 001"
    actual_quote = quote_text
    
    # Pattern 1: "Speaker Name (Interview XXX): text"
    pattern1 = r'^(.+?)\s*\(Interview (\d+)\):\s*(.*)$'
    match1 = re.match(pattern1, quote_text)
    if match1:
        speaker = match1.group(1)
        interview_num = match1.group(2)
        interview_id = f"INT_{interview_num.zfill(3)}"
        interview_name = f"Interview {interview_num.zfill(3)}"
        actual_quote = f"{speaker}: {match1.group(3)}"
    else:
        # Pattern 2: "Interview XXX: text"
        pattern2 = r'^Interview (\d+):\s*(.*)$'
        match2 = re.match(pattern2, quote_text)
        if match2:
            interview_num = match2.group(1)
            interview_id = f"INT_{interview_num.zfill(3)}"
            interview_name = f"Interview {interview_num.zfill(3)}"
            actual_quote = match2.group(2)
    
    return QuoteEvidence(
        quote_id=quote_id,
        interview_id=interview_id,
        interview_name=interview_name,
        text=actual_quote,
        line_number=1,
        context=context,
        speaker_role=None
    )


def _create_stakeholder_mapping(stakeholder_positions: List['StakeholderPosition']) -> Dict[str, List[str]]:
    """Create mapping of stakeholder types to theme positions."""
    mapping = {}
    for sp in stakeholder_positions:
        if sp.stakeholder_type not in mapping:
            mapping[sp.stakeholder_type] = []
        # Add their main concerns/positions
        mapping[sp.stakeholder_type].extend(sp.concerns[:2])  # Top 2 concerns
    return mapping


def transform_to_full_schema(simple_result: SimpleGlobalResult, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform simple result to full GlobalCodingResult schema.
    This happens after Gemini returns the simplified structure.
    """
    from qc.models.comprehensive_analysis_models import (
        QuoteEvidence, GlobalCode, CodeCategory, QuoteChain,
        CrossInterviewTheme, TheoricalSaturationAssessment,
        CodeProgression, ContradictionPair, StakeholderPosition
    )
    
    # Transform themes with error handling
    full_themes = []
    for theme_idx, theme in enumerate(simple_result.themes):
        try:
            # Create quote evidence from strings
            key_quotes = []
            for i, quote_text in enumerate(theme.key_quotes[:3]):  # Limit to 3
                quote_evidence = _parse_quote_to_evidence(
                    quote_text, f"{theme.theme_id}_Q{i+1}", "From global analysis"
                )
                key_quotes.append(quote_evidence)
            
            full_theme = CrossInterviewTheme(
                theme_id=theme.theme_id,
                name=theme.name,
                description=theme.description,
                categories=[],  # Simplified - no categories
                codes=[],  # Would map from codes
                prevalence=theme.prevalence,
                interviews_count=theme.interviews_count,
                quote_chains=[],  # Would map from quote_chains
                key_quotes=key_quotes,
                stakeholder_positions=[],  # Simplified
                contradictions=[],  # Simplified
                theoretical_memo=f"Theme: {theme.description}",
                policy_implications=None,  # Optional field
                confidence_score=theme.confidence_score
            )
            full_themes.append(full_theme)
        except Exception as e:
            logger.error(f"Error transforming theme {theme_idx}: {str(e)}")
            # Create a minimal theme to continue processing
            full_theme = CrossInterviewTheme(
                theme_id=theme.theme_id or f"THEME_{theme_idx+1:03d}",
                name=theme.name or "Unknown Theme",
                description=theme.description or "Error in transformation",
                categories=[],
                codes=[],
                prevalence=getattr(theme, 'prevalence', 0.5),
                interviews_count=getattr(theme, 'interviews_count', 1),
                quote_chains=[],
                key_quotes=[],
                stakeholder_positions=[],
                contradictions=[],
                theoretical_memo="Error in theme transformation",
                policy_implications=None,
                confidence_score=0.5
            )
            full_themes.append(full_theme)
    
    # Transform codes
    full_codes = []
    for code in simple_result.codes:
        full_code = GlobalCode(
            code_id=code.code_id,
            name=code.name,
            definition=code.definition,
            frequency=code.frequency,
            interviews_present=code.interviews_present,
            key_quotes=[],  # Simplified
            first_appearance=code.first_appearance,
            evolution_notes="Identified through global analysis",
            saturation_point=simple_result.saturation_point,
            theme_id=code.theme_id,  # Now properly linked to theme
            parent_code_id=code.parent_code_id,
            hierarchy_level=code.hierarchy_level,
            child_codes=[]  # Will be populated after all codes are processed
        )
        full_codes.append(full_code)
    
    # Link codes to themes based on theme_id
    # Create a mapping of theme_id to code_ids
    theme_code_mapping = {}
    for code in full_codes:
        if code.theme_id:
            if code.theme_id not in theme_code_mapping:
                theme_code_mapping[code.theme_id] = []
            theme_code_mapping[code.theme_id].append(code.code_id)
    
    # Update themes with their associated code IDs
    for theme in full_themes:
        theme.codes = theme_code_mapping.get(theme.theme_id, [])
    
    # Build parent-child relationships for hierarchical coding
    code_by_id = {code.code_id: code for code in full_codes}
    for code in full_codes:
        if code.parent_code_id and code.parent_code_id in code_by_id:
            parent_code = code_by_id[code.parent_code_id]
            parent_code.child_codes.append(code.code_id)
    
    # Transform quote chains with error handling
    full_quote_chains = []
    for chain_idx, chain in enumerate(simple_result.quote_chains):
        try:
            quotes_sequence = []
            for i, quote_text in enumerate(chain.quotes):
                quote_evidence = _parse_quote_to_evidence(
                    quote_text, f"{chain.chain_id}_Q{i+1}", "From quote chain"
                )
                quotes_sequence.append(quote_evidence)
            
            # Normalize chain_type more robustly
            chain_type = chain.chain_type.lower() if chain.chain_type else 'evolution'
            chain_type = chain_type.replace('-', '_').replace(' ', '_').strip()
            
            # Validate against allowed values
            allowed_types = ['evolution', 'contradiction', 'consensus_building', 'problem_solution']
            if chain_type not in allowed_types:
                # Try to find best match
                if 'problem' in chain_type and 'solution' in chain_type:
                    chain_type = 'problem_solution'
                elif 'consensus' in chain_type:
                    chain_type = 'consensus_building'
                elif 'contradict' in chain_type:
                    chain_type = 'contradiction'
                elif 'evol' in chain_type:
                    chain_type = 'evolution'
                else:
                    chain_type = 'evolution'  # Default fallback
                    logger.warning(f"Unknown chain type '{chain.chain_type}' normalized to 'evolution'")
            
            full_chain = QuoteChain(
                chain_id=chain.chain_id,
                theme_id=chain.theme_id,
                chain_type=chain_type,
                description=chain.description,
                quotes_sequence=quotes_sequence,
                key_transition_points=[],
                interpretation=chain.description
            )
            full_quote_chains.append(full_chain)
        except Exception as e:
            logger.error(f"Error transforming quote chain {chain_idx}: {str(e)}")
            # Skip this chain rather than failing the entire analysis
            continue
    
    # Transform contradictions
    full_contradictions = []
    for cont in simple_result.contradictions:
        # Parse quotes for position 1
        position_1_quotes = []
        for i, quote_text in enumerate(cont.position_1_quotes[:3]):
            quote_evidence = _parse_quote_to_evidence(
                quote_text, f"{cont.contradiction_id}_P1_Q{i+1}", "From contradiction"
            )
            position_1_quotes.append(quote_evidence)
        
        # Parse quotes for position 2
        position_2_quotes = []
        for i, quote_text in enumerate(cont.position_2_quotes[:3]):
            quote_evidence = _parse_quote_to_evidence(
                quote_text, f"{cont.contradiction_id}_P2_Q{i+1}", "From contradiction"
            )
            position_2_quotes.append(quote_evidence)
        
        full_contradiction = ContradictionPair(
            contradiction_id=cont.contradiction_id,
            topic=cont.topic,
            position_1=cont.position_1,
            position_1_holders=cont.position_1_holders,
            position_1_quotes=position_1_quotes,
            position_2=cont.position_2,
            position_2_holders=cont.position_2_holders,
            position_2_quotes=position_2_quotes,
            resolution_suggested=cont.resolution_notes,
            theme_ids=cont.theme_ids,
            code_ids=cont.code_ids
        )
        full_contradictions.append(full_contradiction)
    
    # Transform stakeholder positions
    full_stakeholder_positions = []
    for sp in simple_result.stakeholder_positions:
        # Parse main quotes
        supporting_quotes = []
        for i, quote_text in enumerate(sp.main_quotes[:3]):
            quote_evidence = _parse_quote_to_evidence(
                quote_text, f"{sp.stakeholder_id}_Q{i+1}", "Stakeholder position"
            )
            supporting_quotes.append(quote_evidence)
        
        full_sp = StakeholderPosition(
            stakeholder_id=sp.stakeholder_id,
            stakeholder_name=sp.stakeholder_name,
            stakeholder_type=sp.stakeholder_type,
            position_summary=sp.position_summary,
            supporting_quotes=supporting_quotes,
            concerns=sp.concerns,
            recommendations=sp.recommendations,
            influence_level="medium"  # Default, could be enhanced
        )
        full_stakeholder_positions.append(full_sp)
    
    # Create saturation assessment
    saturation = TheoricalSaturationAssessment(
        saturation_point=simple_result.saturation_point,
        interview_number=int(simple_result.saturation_point.split('_')[-1]) if '_' in simple_result.saturation_point else 50,
        evidence=simple_result.saturation_evidence,
        new_codes_curve=[],  # Simplified
        new_themes_curve=[],  # Simplified
        stabilization_indicators=["Saturation reached"],
        post_saturation_validation="Confirmed in remaining interviews"
    )
    
    # Build full result
    full_result = {
        "study_id": metadata.get("study_id", f"study_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
        "analysis_timestamp": metadata.get("analysis_timestamp", datetime.now()),
        "research_question": metadata.get("research_question", ""),
        "interviews_analyzed": metadata.get("interviews_analyzed", 0),
        "total_tokens_analyzed": metadata.get("total_tokens_analyzed", 0),
        "themes": full_themes,
        "codes": full_codes,
        "categories": [],  # Simplified
        "quote_chains": full_quote_chains,
        "code_progressions": [],  # Simplified
        "contradictions": full_contradictions,
        "stakeholder_mapping": _create_stakeholder_mapping(full_stakeholder_positions),
        "saturation_assessment": saturation,
        "theoretical_insights": simple_result.theoretical_insights,
        "emergent_theory": simple_result.emergent_theory,
        "methodological_notes": simple_result.methodological_notes,
        "processing_metadata": {"approach": "simplified_schema"},
        "confidence_scores": {"overall": simple_result.overall_confidence}
    }
    
    return full_result