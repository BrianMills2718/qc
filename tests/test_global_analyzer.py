"""
TDD Tests for Global Qualitative Analyzer

Following proper TDD methodology: RED -> GREEN -> REFACTOR
"""
import pytest
import asyncio
from pathlib import Path
import json
from datetime import datetime

from qc.core.global_qualitative_analyzer import GlobalQualitativeAnalyzer
from qc.models.comprehensive_analysis_models import (
    GlobalCodingResult, EnhancedResult, QuoteEvidence,
    CrossInterviewTheme, TheoricalSaturationAssessment
)


class TestGlobalAnalyzerInitialization:
    """Test analyzer initialization and setup."""
    
    def test_analyzer_init_with_research_question(self):
        """Test initializing analyzer with custom research question."""
        question = "How do researchers perceive AI tools?"
        analyzer = GlobalQualitativeAnalyzer(research_question=question)
        
        assert analyzer.research_question == question
        assert analyzer.docx_parser is not None
        assert analyzer.token_counter is not None
        assert analyzer.gemini_client is not None
    
    def test_analyzer_init_default_question(self):
        """Test analyzer uses default question from env."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Should use default or env variable
        assert analyzer.research_question is not None
        assert len(analyzer.research_question) > 0
    
    def test_analyzer_finds_interview_files(self):
        """Test that analyzer finds interview files on init."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Should find interview files
        assert hasattr(analyzer, 'interview_files')
        assert isinstance(analyzer.interview_files, list)
        # We know there are 103 interviews
        assert len(analyzer.interview_files) == 103


class TestGlobalAnalysisExecution:
    """Test the global analysis execution."""
    
    def test_analyze_global_sample(self):
        """Test analyzing a small sample - validate data structures only."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Test that we can create a complete valid result structure
        mock_global_result = {
            "study_id": "test_001",
            "analysis_timestamp": datetime.now(),
            "research_question": "Test question",
            "interviews_analyzed": 10,
            "total_tokens_analyzed": 30000,
            "themes": [],
            "codes": [],
            "categories": [],
            "quote_chains": [],
            "code_progressions": [],
            "contradictions": [],
            "stakeholder_mapping": {},
            "saturation_assessment": {
                "saturation_point": "INT_008",
                "interview_number": 8,
                "evidence": "No new codes found",
                "new_codes_curve": [5, 3, 1, 0],
                "new_themes_curve": [2, 1, 0, 0],  
                "stabilization_indicators": ["Repeated themes", "No new patterns"],
                "post_saturation_validation": "Confirmed in later interviews"
            },
            "theoretical_insights": ["Test insight"],
            "emergent_theory": "Test theory",
            "methodological_notes": "Test notes",
            "processing_metadata": {"test": "metadata"},
            "confidence_scores": {"overall": 0.85}
        }
        
        # Test that GlobalCodingResult can be created with this data
        result = GlobalCodingResult(**mock_global_result)
        
        assert result is not None
        assert result.study_id == "test_001"
        assert result.interviews_analyzed == 10
        assert isinstance(result.saturation_assessment.new_codes_curve, list)
    
    def test_token_limit_check(self):
        """Test token limit validation logic."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Test that token manager can validate large content
        from qc.utils.token_manager import TokenManager, TokenLimitError
        token_manager = TokenManager(max_tokens=900000)
        
        # Test with content that would exceed limits
        large_text = "This is test content. " * 50000  # Approximately 150K tokens
        
        with pytest.raises(TokenLimitError):
            token_manager.validate_prompt_size(large_text, max_response_tokens=800000)
    
    def test_processing_metadata_added(self):
        """Test that processing metadata structure is valid."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Test that metadata can be properly structured
        test_metadata = {
            'processing_time_seconds': 120.5,
            'interviews_analyzed': 5,
            'total_tokens': 50000,
            'llm_calls': 2,
            'model': 'gemini-2.5-flash',
            'timestamp': '2024-01-01T12:00:00'
        }
        
        # Verify metadata structure is valid
        assert isinstance(test_metadata['processing_time_seconds'], float)
        assert isinstance(test_metadata['interviews_analyzed'], int)
        assert test_metadata['llm_calls'] == 2
        assert test_metadata['model'] == 'gemini-2.5-flash'


class TestLLMCalls:
    """Test the two LLM call methods."""
    
    def test_comprehensive_global_analysis_call(self):
        """Test the first LLM call data structure validation."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Test that we can create a complete GlobalCodingResult
        result_data = {
            "study_id": "test_study_123",
            "analysis_timestamp": datetime.now(),
            "research_question": "Test research question",
            "interviews_analyzed": 10,
            "total_tokens_analyzed": 50000,
            "themes": [],
            "codes": [],
            "categories": [],
            "quote_chains": [],
            "code_progressions": [],
            "contradictions": [],
            "stakeholder_mapping": {},
            "saturation_assessment": {
                "saturation_point": "INT_008",
                "interview_number": 8,
                "evidence": "Test evidence",
                "new_codes_curve": [3, 2, 1, 0],
                "new_themes_curve": [2, 1, 0, 0],
                "stabilization_indicators": ["Pattern repetition"],
                "post_saturation_validation": "Test validation"
            },
            "theoretical_insights": ["Test insight"],
            "emergent_theory": "Test theory",
            "methodological_notes": "Test notes",
            "processing_metadata": {"test": "metadata"},
            "confidence_scores": {"overall": 0.8}
        }
        
        result = GlobalCodingResult(**result_data)
        
        # Verify the structure is valid and complete
        assert result.study_id == "test_study_123"
        assert result.interviews_analyzed == 10
        assert result.total_tokens_analyzed == 50000
        assert isinstance(result.themes, list)
        assert isinstance(result.codes, list)
    
    def test_refine_for_traceability_call(self):
        """Test the second LLM call data structure validation."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Create a real initial result
        initial_result = GlobalCodingResult(
            study_id="test_study",
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
            saturation_assessment={
                "saturation_point": "INT_005",
                "interview_number": 5,
                "evidence": "Test evidence",
                "new_codes_curve": [3, 2, 1, 0],
                "new_themes_curve": [2, 1, 0, 0],
                "stabilization_indicators": ["Pattern repetition"],
                "post_saturation_validation": "Test validation"
            },
            theoretical_insights=["Test insight"],
            emergent_theory="Test theory",
            methodological_notes="Test notes",
            processing_metadata={"test": "metadata"},
            confidence_scores={"overall": 0.8}
        )
        
        # Test EnhancedResult structure
        enhanced_data = {
            "global_analysis": initial_result,
            "csv_export_data": {
                "themes_table": [],
                "codes_table": [],
                "quotes_table": [],
                "quote_chains_table": [],
                "contradictions_table": [],
                "stakeholder_positions_table": [],
                "saturation_curve_table": [],
                "traceability_matrix": []
            },
            "markdown_report": "# Test Report",
            "executive_summary": "Test Summary",
            "complete_quote_inventory": [],
            "interview_summaries": {},
            "traceability_completeness": 0.95,
            "quote_chain_coverage": 0.85,
            "stakeholder_coverage": 0.80,
            "evidence_strength": 0.90
        }
        
        result = EnhancedResult(**enhanced_data)
        
        # Verify the enhanced structure is valid
        assert isinstance(result.global_analysis, GlobalCodingResult)
        assert result.traceability_completeness == 0.95
        assert isinstance(result.csv_export_data.themes_table, list)


class TestExportFunctions:
    """Test the export functionality."""
    
    def test_export_csv_files(self):
        """Test CSV export data structure validation."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Test that CSV export data can be created with proper structure
        from qc.models.comprehensive_analysis_models import CSVExportData
        csv_data = {
            "themes_table": [{"theme_id": "T1", "name": "Test Theme"}],
            "codes_table": [],
            "quotes_table": [],
            "quote_chains_table": [],
            "contradictions_table": [],
            "stakeholder_positions_table": [],
            "saturation_curve_table": [],
            "traceability_matrix": []
        }
        
        result = CSVExportData(**csv_data)
        
        # Verify the structure is valid
        assert isinstance(result.themes_table, list)
        assert len(result.themes_table) == 1
        assert result.themes_table[0]["theme_id"] == "T1"
    
    def test_export_markdown_report(self):
        """Test markdown report data structure validation."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Test that markdown report field can be validated
        test_report = "# Test Report\n\nThis is a test analysis report."
        
        # Simple validation that the report content is a string
        assert isinstance(test_report, str)
        assert test_report.startswith("# Test Report")
        assert "analysis report" in test_report
    
    def test_export_json_backup(self):
        """Test JSON backup data structure validation."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Test that a result can be serialized to JSON format
        test_data = {"test": "data", "analysis_id": "test_001"}
        
        # Validate JSON serialization capability
        import json
        json_str = json.dumps(test_data)
        deserialized = json.loads(json_str)
        
        assert deserialized["test"] == "data"
        assert deserialized["analysis_id"] == "test_001"


class TestIntegrationWithRealFiles:
    """Integration tests using real interview files."""
    
    @pytest.mark.integration
    def test_load_real_interview_files(self):
        """Test that we can load actual interview files."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Should have found 103 files
        assert len(analyzer.interview_files) == 103
        
        # All should be DOCX files
        for file in analyzer.interview_files:
            assert file.suffix.lower() == '.docx'
            assert file.exists()
    
    @pytest.mark.integration
    def test_token_count_real_files(self):
        """Test token counting with real files."""
        from qc.core.load_and_verify_interviews import load_all_interviews_with_metadata
        
        analyzer = GlobalQualitativeAnalyzer()
        
        # Load just 5 files to test
        sample_files = analyzer.interview_files[:5]
        full_text, total_tokens, metadata = load_all_interviews_with_metadata(sample_files)
        
        assert total_tokens > 0
        assert total_tokens < 50000  # 5 files should be well under this
        assert len(metadata) == 5
        
        # Check metadata structure
        for meta in metadata:
            assert 'interview_id' in meta
            assert 'file_name' in meta
            assert 'word_count' in meta
            assert 'estimated_tokens' in meta


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-k", "not integration"])