"""
TDD Tests for Comprehensive Analysis Models

Following proper TDD: Write tests FIRST, then implementation.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from qc.models.comprehensive_analysis_models import (
    QuoteEvidence, GlobalCode, CodeCategory, QuoteChain,
    StakeholderPosition, ContradictionPair, CrossInterviewTheme,
    TheoricalSaturationAssessment, CodeProgression, GlobalCodingResult,
    CSVExportData, EnhancedResult
)


class TestQuoteEvidence:
    """Test QuoteEvidence model validation and functionality."""
    
    def test_quote_evidence_creation(self):
        """Test creating a QuoteEvidence with all fields."""
        quote = QuoteEvidence(
            quote_id="Q_001_045",
            interview_id="INT_001", 
            interview_name="Interview_001.docx",
            text="We need better AI tools for qualitative research",
            line_number=45,
            context="Discussion about research methods",
            speaker_role="Senior Researcher"
        )
        
        assert quote.quote_id == "Q_001_045"
        assert quote.interview_id == "INT_001"
        assert quote.line_number == 45
        assert quote.speaker_role == "Senior Researcher"
    
    def test_quote_evidence_minimal(self):
        """Test creating QuoteEvidence with only required fields."""
        quote = QuoteEvidence(
            quote_id="Q_002_100",
            interview_id="INT_002",
            interview_name="Interview_002.docx", 
            text="AI is transforming our work",
            line_number=100,
            context="AI discussion"
        )
        
        assert quote.speaker_role is None  # Optional field
    
    def test_quote_evidence_validation(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            QuoteEvidence(
                quote_id="Q_003",
                # Missing required fields
            )


class TestGlobalCode:
    """Test GlobalCode model validation and functionality."""
    
    def test_global_code_creation(self):
        """Test creating a GlobalCode with quotes."""
        quotes = [
            QuoteEvidence(
                quote_id="Q_001_045",
                interview_id="INT_001",
                interview_name="Interview_001.docx",
                text="AI tools are essential",
                line_number=45,
                context="Methods discussion"
            )
        ]
        
        code = GlobalCode(
            code_id="CODE_001",
            name="AI_tool_importance",
            definition="References to AI tools being essential for research",
            frequency=15,
            interviews_present=["INT_001", "INT_005", "INT_010"],
            key_quotes=quotes,
            first_appearance="INT_001",
            evolution_notes="Started as skepticism, evolved to acceptance"
        )
        
        assert code.frequency == 15
        assert len(code.interviews_present) == 3
        assert len(code.key_quotes) == 1
    
    def test_global_code_saturation(self):
        """Test code with saturation point."""
        code = GlobalCode(
            code_id="CODE_002",
            name="data_quality_concerns",
            definition="Concerns about data quality in AI analysis",
            frequency=25,
            interviews_present=["INT_001", "INT_002"],
            key_quotes=[],
            first_appearance="INT_001",
            evolution_notes="Consistent concern",
            saturation_point="INT_045"
        )
        
        assert code.saturation_point == "INT_045"


class TestQuoteChain:
    """Test QuoteChain model for progression tracking."""
    
    def test_evolution_chain(self):
        """Test creating an evolution chain."""
        quotes = [
            QuoteEvidence(
                quote_id=f"Q_{i:03d}_100",
                interview_id=f"INT_{i:03d}",
                interview_name=f"Interview_{i:03d}.docx",
                text=f"Evolution stage {i}",
                line_number=100,
                context="Evolution context"
            )
            for i in range(1, 4)
        ]
        
        chain = QuoteChain(
            chain_id="CHAIN_001",
            theme_id="THEME_001",
            chain_type="evolution",
            description="How AI adoption evolved",
            quotes_sequence=quotes,
            key_transition_points=["INT_010", "INT_045"],
            interpretation="Shows progression from skepticism to adoption"
        )
        
        assert chain.chain_type == "evolution"
        assert len(chain.quotes_sequence) == 3
        assert len(chain.key_transition_points) == 2
    
    def test_contradiction_chain(self):
        """Test creating a contradiction chain."""
        chain = QuoteChain(
            chain_id="CHAIN_002",
            theme_id="THEME_002",
            chain_type="contradiction",
            description="Opposing views on AI reliability",
            quotes_sequence=[],
            key_transition_points=[],
            interpretation="Fundamental disagreement remains"
        )
        
        assert chain.chain_type == "contradiction"


class TestContradictionPair:
    """Test ContradictionPair model."""
    
    def test_contradiction_with_evidence(self):
        """Test creating contradiction with evidence from both sides."""
        evidence_a = [
            QuoteEvidence(
                quote_id="Q_001_050",
                interview_id="INT_001",
                interview_name="Interview_001.docx",
                text="AI improves efficiency",
                line_number=50,
                context="Benefits discussion"
            )
        ]
        
        evidence_b = [
            QuoteEvidence(
                quote_id="Q_002_075",
                interview_id="INT_002", 
                interview_name="Interview_002.docx",
                text="AI reduces quality",
                line_number=75,
                context="Concerns discussion"
            )
        ]
        
        contradiction = ContradictionPair(
            contradiction_id="CONTRA_001",
            theme_id="THEME_003",
            issue="AI impact on research quality",
            position_a="AI improves research",
            position_b="AI degrades research",
            evidence_a=evidence_a,
            evidence_b=evidence_b,
            stakeholders_a=["Researchers", "Tech advocates"],
            stakeholders_b=["Traditionalists", "Quality advocates"]
        )
        
        assert len(contradiction.evidence_a) == 1
        assert len(contradiction.evidence_b) == 1
        assert len(contradiction.stakeholders_a) == 2


class TestGlobalCodingResult:
    """Test the main global coding result model."""
    
    def test_minimal_global_result(self):
        """Test creating minimal valid global result."""
        result = GlobalCodingResult(
            study_id="study_001",
            analysis_timestamp=datetime.now(),
            research_question="How is AI used in research?",
            interviews_analyzed=103,
            total_tokens_analyzed=318000,
            themes=[],
            codes=[],
            categories=[],
            quote_chains=[],
            code_progressions=[],
            contradictions=[],
            stakeholder_mapping={},
            saturation_assessment=TheoricalSaturationAssessment(
                saturation_point="INT_045",
                interview_number=45,
                evidence="No new codes after interview 45",
                new_codes_curve=[10, 8, 5, 2, 0],
                new_themes_curve=[3, 2, 1, 0, 0],
                stabilization_indicators=["Repeated themes", "No new insights"],
                post_saturation_validation="Remaining interviews confirmed"
            ),
            theoretical_insights=["AI adoption is context-dependent"],
            emergent_theory="Technology adoption in research settings",
            methodological_notes="Used grounded theory approach",
            processing_metadata={},
            confidence_scores={}
        )
        
        assert result.interviews_analyzed == 103
        assert result.total_tokens_analyzed == 318000
        assert result.saturation_assessment.interview_number == 45
    
    def test_global_result_with_themes(self):
        """Test global result with themes and codes."""
        theme = CrossInterviewTheme(
            theme_id="THEME_001",
            name="AI Integration Challenges",
            description="Challenges in integrating AI into research",
            categories=[],
            codes=["CODE_001", "CODE_002"],
            prevalence=0.85,
            interviews_count=88,
            quote_chains=["CHAIN_001"],
            key_quotes=[],
            stakeholder_positions=[],
            contradictions=["CONTRA_001"],
            theoretical_memo="Integration faces technical and cultural barriers",
            confidence_score=0.92
        )
        
        result = GlobalCodingResult(
            study_id="study_002",
            analysis_timestamp=datetime.now(),
            research_question="AI in research",
            interviews_analyzed=103,
            total_tokens_analyzed=318000,
            themes=[theme],
            codes=[],
            categories=[],
            quote_chains=[],
            code_progressions=[],
            contradictions=[],
            stakeholder_mapping={},
            saturation_assessment=TheoricalSaturationAssessment(
                saturation_point="INT_050",
                interview_number=50,
                evidence="Saturation reached",
                new_codes_curve=[],
                new_themes_curve=[],
                stabilization_indicators=[],
                post_saturation_validation="Confirmed"
            ),
            theoretical_insights=[],
            emergent_theory="",
            methodological_notes="",
            processing_metadata={},
            confidence_scores={}
        )
        
        assert len(result.themes) == 1
        assert result.themes[0].prevalence == 0.85


class TestEnhancedResult:
    """Test the enhanced result with CSV export data."""
    
    def test_enhanced_result_quality_metrics(self):
        """Test enhanced result with quality metrics."""
        global_result = GlobalCodingResult(
            study_id="study_003",
            analysis_timestamp=datetime.now(),
            research_question="Test question",
            interviews_analyzed=10,
            total_tokens_analyzed=50000,
            themes=[],
            codes=[],
            categories=[],
            quote_chains=[],
            code_progressions=[],
            contradictions=[],
            stakeholder_mapping={},
            saturation_assessment=TheoricalSaturationAssessment(
                saturation_point="INT_008",
                interview_number=8,
                evidence="Saturation",
                new_codes_curve=[],
                new_themes_curve=[],
                stabilization_indicators=[],
                post_saturation_validation="Valid"
            ),
            theoretical_insights=[],
            emergent_theory="",
            methodological_notes="",
            processing_metadata={},
            confidence_scores={}
        )
        
        enhanced = EnhancedResult(
            global_analysis=global_result,
            csv_export_data=CSVExportData(
                themes_table=[],
                codes_table=[],
                quotes_table=[],
                quote_chains_table=[],
                contradictions_table=[],
                stakeholder_positions_table=[],
                saturation_curve_table=[],
                traceability_matrix=[]
            ),
            markdown_report="# Analysis Report",
            executive_summary="Summary of findings",
            complete_quote_inventory=[],
            interview_summaries={},
            traceability_completeness=0.95,
            quote_chain_coverage=0.88,
            stakeholder_coverage=0.75,
            evidence_strength=0.90
        )
        
        assert enhanced.traceability_completeness == 0.95
        assert enhanced.quote_chain_coverage == 0.88
        assert enhanced.evidence_strength == 0.90
    
    def test_csv_export_data_structure(self):
        """Test CSV export data has correct structure."""
        csv_data = CSVExportData(
            themes_table=[{"theme_id": "T1", "name": "Test Theme"}],
            codes_table=[{"code_id": "C1", "name": "Test Code"}],
            quotes_table=[{"quote_id": "Q1", "text": "Test quote"}],
            quote_chains_table=[],
            contradictions_table=[],
            stakeholder_positions_table=[],
            saturation_curve_table=[],
            traceability_matrix=[]
        )
        
        assert len(csv_data.themes_table) == 1
        assert csv_data.themes_table[0]["theme_id"] == "T1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])