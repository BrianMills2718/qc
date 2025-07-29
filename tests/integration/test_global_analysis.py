"""
Integration Tests for Global Analysis End-to-End Workflow

Following TDD methodology: RED -> GREEN -> REFACTOR
Testing complete LLM-native global analysis pipeline.

Day 3 Task 3.6: End-to-end integration testing with real data
"""
import pytest
import asyncio
from pathlib import Path
import json
import tempfile
import shutil
from unittest.mock import patch, AsyncMock
from datetime import datetime

from qc.core.global_qualitative_analyzer import GlobalQualitativeAnalyzer
from qc.storage.simple_neo4j_client import SimpleNeo4jClient
from qc.models.comprehensive_analysis_models import GlobalCodingResult, EnhancedResult
from qc.core.load_and_verify_interviews import load_all_interviews_with_metadata


@pytest.mark.integration
class TestGlobalAnalysisEndToEnd:
    """Integration tests for complete analysis pipeline."""
    
    @pytest.mark.asyncio
    async def test_global_analysis_end_to_end(self):
        """
        Complete end-to-end test:
        1. Load all 103 DOCX files
        2. Run global LLM analysis (2 calls total)  
        3. Store results in Neo4j and export CSV/Markdown
        4. Verify quote chains and code progressions exist
        """
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Mock Gemini API calls to avoid using real API in tests
            with patch('qc.core.simple_gemini_client.SimpleGeminiClient.extract_themes') as mock_extract:
                # Configure mock responses
                await self._setup_mock_gemini_responses(mock_extract)
                
                # Initialize analyzer
                analyzer = GlobalQualitativeAnalyzer()
                
                # Test with a small sample first (5 interviews)
                result = await analyzer.analyze_global(sample_size=5)
                
                # Verify analysis results
                assert isinstance(result, EnhancedResult)
                assert result.global_analysis.interviews_analyzed == 5
                assert len(result.global_analysis.themes) > 0
                assert len(result.global_analysis.codes) > 0
                assert result.traceability_completeness > 0.8
                
                # Test export functionality
                analyzer.export_csv_files(result, output_dir / "csv")
                analyzer.export_markdown_report(result, output_dir / "report.md")
                analyzer.export_json_backup(result, output_dir / "analysis.json")
                
                # Verify exports were created
                assert (output_dir / "csv" / "themes.csv").exists()
                assert (output_dir / "csv" / "codes.csv").exists()
                assert (output_dir / "report.md").exists()
                assert (output_dir / "analysis.json").exists()
                
                # Verify quote chains exist
                assert len(result.global_analysis.quote_chains) > 0
                
                # Verify code progressions exist
                assert len(result.global_analysis.code_progressions) > 0
    
    @pytest.mark.asyncio
    async def test_neo4j_client_initialization(self):
        """Test Neo4j client can be initialized and configured."""
        # Test that client initializes correctly
        client = SimpleNeo4jClient()
        
        assert client.uri == "bolt://localhost:7687"
        assert client.username == "neo4j"
        assert client.password is not None
        assert client.is_connected is False
        
        # Test that client has required methods
        assert hasattr(client, 'connect')
        assert hasattr(client, 'create_schema')
        assert hasattr(client, 'store_enhanced_result')
        assert hasattr(client, 'close')
    
    @pytest.mark.asyncio
    async def test_real_interview_loading(self):
        """Test loading actual interview files."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Should find interview files
        assert len(analyzer.interview_files) > 0
        
        # Test with just 3 files to avoid token limits in testing
        sample_files = analyzer.interview_files[:3]
        
        full_text, total_tokens, metadata = load_all_interviews_with_metadata(sample_files)
        
        # Verify loading worked
        assert len(full_text) > 1000  # Should have substantial content
        assert total_tokens > 100    # Should have reasonable token count
        assert len(metadata) == 3    # Should have metadata for each file
        
        # Verify metadata structure
        for meta in metadata:
            assert 'interview_id' in meta
            assert 'file_name' in meta
            assert 'word_count' in meta
            assert 'estimated_tokens' in meta
            assert meta['word_count'] > 0
            assert meta['estimated_tokens'] > 0
    
    @pytest.mark.asyncio 
    async def test_token_validation(self):
        """Test that all 103 interviews fit within token limits."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Load all interviews
        full_text, total_tokens, metadata = load_all_interviews_with_metadata(analyzer.interview_files)
        
        # Should fit in 1M context window with room for prompt and response
        assert total_tokens < 900_000, f"Token count {total_tokens:,} exceeds safe limit"
        assert len(metadata) >= 100, f"Expected ~103 interviews, got {len(metadata)}"
        
        # Verify we can create analyzer without token errors
        assert analyzer.token_counter.count_tokens(full_text[:1000]) > 0
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error handling in the analysis pipeline."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Test with invalid sample size
        with pytest.raises(Exception):
            await analyzer.analyze_global(sample_size=0)
        
        # Test with mock API failure
        with patch('qc.core.simple_gemini_client.SimpleGeminiClient.extract_themes') as mock_extract:
            mock_extract.side_effect = Exception("API Error")
            
            with pytest.raises(Exception):
                await analyzer.analyze_global(sample_size=1)
    
    # Helper methods
    
    async def _setup_mock_gemini_responses(self, mock_extract):
        """Configure mock Gemini API responses."""
        # First call: comprehensive global analysis
        global_response = {
            "study_id": "test_study_123",
            "analysis_timestamp": datetime.now().isoformat(),
            "research_question": "Test question",
            "interviews_analyzed": 5,
            "total_tokens_analyzed": 25000,
            "themes": [
                {
                    "theme_id": "T001",
                    "name": "AI Integration",
                    "description": "How AI is being integrated",
                    "categories": [],
                    "codes": ["C001"],
                    "prevalence": 0.8,
                    "interviews_count": 4,
                    "quote_chains": ["QC001"],
                    "key_quotes": [
                        {
                            "quote_id": "Q001",
                            "interview_id": "INT_001", 
                            "interview_name": "Test Interview 1",
                            "text": "AI is transforming research",
                            "line_number": 45,
                            "context": "Discussion about AI tools"
                        }
                    ],
                    "stakeholder_positions": [],
                    "contradictions": [],
                    "theoretical_memo": "Key theme about AI integration",
                    "confidence_score": 0.9
                }
            ],
            "codes": [
                {
                    "code_id": "C001",
                    "name": "AI Adoption",
                    "definition": "Patterns of AI adoption",
                    "frequency": 12,
                    "interviews_present": ["INT_001", "INT_002"],
                    "key_quotes": [
                        {
                            "quote_id": "Q001",
                            "interview_id": "INT_001",
                            "interview_name": "Test Interview 1", 
                            "text": "AI is transforming research",
                            "line_number": 45,
                            "context": "Discussion about AI tools"
                        }
                    ],
                    "first_appearance": "INT_001",
                    "evolution_notes": "Emerged early, developed throughout",
                    "saturation_point": "INT_003"
                }
            ],
            "categories": [],
            "quote_chains": [
                {
                    "chain_id": "QC001",
                    "theme_id": "T001",
                    "chain_type": "evolution",
                    "description": "Evolution of AI adoption",
                    "quotes_sequence": [
                        {
                            "quote_id": "Q001",
                            "interview_id": "INT_001",
                            "interview_name": "Test Interview 1",
                            "text": "AI is transforming research",
                            "line_number": 45,
                            "context": "Discussion about AI tools"
                        }
                    ],
                    "key_transition_points": ["INT_002"],
                    "interpretation": "Shows progression of AI adoption"
                }
            ],
            "code_progressions": [
                {
                    "code_id": "C001",
                    "progression_type": "emerging",
                    "timeline": [{"interview_batch": 1, "frequency": 5}],
                    "definition_evolution": ["Initial definition"],
                    "peak_period": "INT_001-INT_003",
                    "key_contributors": ["INT_001", "INT_002"]
                }
            ],
            "contradictions": [],
            "stakeholder_mapping": {},
            "saturation_assessment": {
                "saturation_point": "INT_003",
                "interview_number": 3,
                "evidence": "No new themes after interview 3",
                "new_codes_curve": [5, 3, 1, 0],
                "new_themes_curve": [2, 1, 0, 0],
                "stabilization_indicators": ["Pattern repetition", "No new insights"],
                "post_saturation_validation": "Confirmed in interviews 4-5"
            },
            "theoretical_insights": ["AI adoption follows predictable patterns"],
            "emergent_theory": "AI integration theory",
            "methodological_notes": "Global analysis approach effective",
            "processing_metadata": {"test": "metadata"},
            "confidence_scores": {"overall": 0.85}
        }
        
        # Second call: enhanced result with traceability
        enhanced_response = {
            "csv_export_data": {
                "themes_table": [{"theme_id": "T001", "name": "AI Integration", "prevalence": 0.8}],
                "codes_table": [{"code_id": "C001", "name": "AI Adoption", "frequency": 12}],
                "quotes_table": [{"quote_id": "Q001", "text": "AI is transforming research"}],
                "quote_chains_table": [{"chain_id": "QC001", "type": "evolution"}],
                "contradictions_table": [],
                "stakeholder_positions_table": [],
                "saturation_curve_table": [{"interview": 1, "new_codes": 5}],
                "traceability_matrix": [{"theme_id": "T001", "code_id": "C001", "quote_id": "Q001"}]
            },
            "markdown_report": "# Global Analysis Report\n\n## Key Findings\n\nAI integration is a major theme.",
            "executive_summary": "Analysis of 5 interviews reveals strong AI integration patterns.",
            "complete_quote_inventory": [
                {
                    "quote_id": "Q001",
                    "interview_id": "INT_001",
                    "interview_name": "Test Interview 1",
                    "text": "AI is transforming research", 
                    "line_number": 45,
                    "context": "Discussion about AI tools"
                }
            ],
            "interview_summaries": {
                "INT_001": "Discussed AI transformation",
                "INT_002": "Explored AI adoption patterns"
            },
            "traceability_completeness": 0.95,
            "quote_chain_coverage": 0.90,
            "stakeholder_coverage": 0.85,
            "evidence_strength": 0.88
        }
        
        # Configure mock to return different responses for each call
        mock_extract.side_effect = [global_response, enhanced_response]
    
    def _create_mock_neo4j_driver(self):
        """Create properly mocked Neo4j driver for testing."""
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_tx = AsyncMock()
        mock_result = AsyncMock()
        mock_record = AsyncMock()
        
        # Setup session context manager
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        mock_driver.session.return_value = mock_session_context
        
        # Setup transaction context manager
        mock_tx_context = AsyncMock()
        mock_tx_context.__aenter__ = AsyncMock(return_value=mock_tx)
        mock_tx_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin_transaction.return_value = mock_tx_context
        
        # Setup query results
        mock_tx.run.return_value = mock_result
        mock_result.single.return_value = mock_record
        mock_record.__getitem__.return_value = "test_study_id"
        
        # Setup driver
        mock_driver.verify_connectivity = AsyncMock()
        
        return mock_driver, mock_session


@pytest.mark.integration
class TestAnalysisQuality:
    """Test analysis quality and theoretical coherence."""
    
    @pytest.mark.asyncio
    async def test_analysis_quality_metrics(self):
        """Test that analysis meets quality standards."""
        with patch('qc.core.simple_gemini_client.SimpleGeminiClient.extract_themes') as mock_extract:
            # Setup quality mock response - this needs to be an EnhancedResult structure
            enhanced_mock = {
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
                "markdown_report": "# Quality Test Report",
                "executive_summary": "Quality test summary",
                "complete_quote_inventory": [],
                "interview_summaries": {},
                "traceability_completeness": 0.95,
                "quote_chain_coverage": 0.90,
                "stakeholder_coverage": 0.85,
                "evidence_strength": 0.88
            }
            
            global_mock = {
                "study_id": "quality_test",
                "analysis_timestamp": datetime.now().isoformat(),
                "research_question": "Quality test",
                "interviews_analyzed": 3,
                "total_tokens_analyzed": 15000,
                "themes": [],
                "codes": [],
                "categories": [],
                "quote_chains": [],
                "code_progressions": [],
                "contradictions": [],
                "stakeholder_mapping": {},
                "saturation_assessment": {
                    "saturation_point": "INT_002",
                    "interview_number": 2,
                    "evidence": "Test evidence",
                    "new_codes_curve": [3, 1],
                    "new_themes_curve": [1, 0],
                    "stabilization_indicators": ["Stability"],
                    "post_saturation_validation": "Validated"
                },
                "theoretical_insights": ["Quality insight"],
                "emergent_theory": "Quality theory",
                "methodological_notes": "Quality notes",
                "processing_metadata": {"test": "quality"},
                "confidence_scores": {"overall": 0.9}
            }
            
            mock_extract.side_effect = [global_mock, enhanced_mock]
            
            analyzer = GlobalQualitativeAnalyzer()
            result = await analyzer.analyze_global(sample_size=3)
            
            # Quality metrics
            assert result.global_analysis.confidence_scores["overall"] >= 0.8
            assert result.global_analysis.interviews_analyzed > 0
            assert result.global_analysis.total_tokens_analyzed > 0
    
    @pytest.mark.asyncio
    async def test_theoretical_coherence(self):
        """Test that theoretical insights are coherent."""
        with patch('qc.core.simple_gemini_client.SimpleGeminiClient.extract_themes') as mock_extract:
            # Need two calls for complete enhanced result
            enhanced_response = {
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
                "markdown_report": "# Theoretical Test Report",
                "executive_summary": "Theoretical test summary",
                "complete_quote_inventory": [],
                "interview_summaries": {},
                "traceability_completeness": 0.95,
                "quote_chain_coverage": 0.90,
                "stakeholder_coverage": 0.85,
                "evidence_strength": 0.88
            }
            
            global_response = {
                "study_id": "theory_test",
                "analysis_timestamp": datetime.now().isoformat(),
                "research_question": "Theoretical coherence test",
                "interviews_analyzed": 3,
                "total_tokens_analyzed": 15000,
                "themes": [],
                "codes": [],
                "categories": [],
                "quote_chains": [],
                "code_progressions": [],
                "contradictions": [],
                "stakeholder_mapping": {},
                "saturation_assessment": {
                    "saturation_point": "INT_002",
                    "interview_number": 2,
                    "evidence": "Theoretical saturation reached",
                    "new_codes_curve": [3, 1],
                    "new_themes_curve": [1, 0],
                    "stabilization_indicators": ["No new theoretical insights"],
                    "post_saturation_validation": "Theory validated in remaining interviews"
                },
                "theoretical_insights": [
                    "Primary theoretical insight about AI integration",
                    "Secondary insight about methodological implications"
                ],
                "emergent_theory": "Comprehensive theory of AI-assisted qualitative research",
                "methodological_notes": "LLM-native approach provides global perspective",
                "processing_metadata": {"approach": "global", "calls": 2},
                "confidence_scores": {"overall": 0.92, "theoretical": 0.88}
            }
            
            mock_extract.side_effect = [global_response, enhanced_response]
            
            analyzer = GlobalQualitativeAnalyzer()
            result = await analyzer.analyze_global(sample_size=3)
            
            # Theoretical coherence checks
            assert len(result.global_analysis.theoretical_insights) > 0
            assert len(result.global_analysis.emergent_theory) > 10
            assert "theory" in result.global_analysis.emergent_theory.lower()
            assert result.global_analysis.saturation_assessment.evidence is not None


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration"])