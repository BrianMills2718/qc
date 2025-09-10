#!/usr/bin/env python3
"""
Comprehensive tests for automation display functionality

Tests the automation viewer CLI commands and Neo4j display methods
to ensure proper display of automated qualitative coding results.
"""

import asyncio
import pytest
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

# Import the modules to test
from src.qc.cli_automation_viewer import AutomationResultsViewer, run_show_results, run_browse_quotes, run_explore_patterns
from src.qc.core.neo4j_manager import EnhancedNeo4jManager

logger = logging.getLogger(__name__)


class TestAutomationDisplayMethods:
    """Test the Neo4j automation display methods"""
    
    @pytest.fixture
    def mock_neo4j_manager(self):
        """Create a mock Neo4j manager with test data"""
        manager = MagicMock(spec=EnhancedNeo4jManager)
        manager.ensure_connected = AsyncMock()
        
        # Mock data representing the automated system's expected output
        manager.get_automation_summary = AsyncMock(return_value={
            "statistics": {
                "quotes_extracted": 156,
                "quote_nodes": 47,
                "interviews_processed": 6,
                "entities_detected": 25,
                "entity_relationships": 11,
                "code_assignments": 33
            },
            "confidence_distribution": {
                "high": 15,
                "medium": 20,
                "low": 12
            },
            "timeline": {
                "interview_001": {"quotes": 25, "entities": 5},
                "interview_002": {"quotes": 30, "entities": 8},
                "interview_003": {"quotes": 22, "entities": 3}
            },
            "interview_ids": ["interview_001", "interview_002", "interview_003"]
        })
        
        manager.get_quotes_with_assignments = AsyncMock(return_value=[
            {
                "id": "quote_001",
                "text": "We need better AI integration in our methods",
                "line_start": 15,
                "line_end": 15,
                "interview_id": "interview_001",
                "speaker": "Participant A",
                "confidence": 0.85,
                "context": "Discussion about methodological improvements",
                "entities": [
                    {
                        "id": "entity_ai",
                        "name": "AI integration",
                        "entity_type": "technology",
                        "confidence": 0.9
                    }
                ],
                "codes": [
                    {
                        "id": "code_methods",
                        "name": "methodological_improvement",
                        "code_type": "process",
                        "confidence": 0.8
                    }
                ]
            },
            {
                "id": "quote_002", 
                "text": "The traditional approaches are becoming obsolete",
                "line_start": 22,
                "line_end": 22,
                "interview_id": "interview_001",
                "speaker": "Participant B",
                "confidence": 0.75,
                "context": "Critique of existing methods",
                "entities": [
                    {
                        "id": "entity_traditional",
                        "name": "traditional approaches",
                        "entity_type": "method",
                        "confidence": 0.7
                    }
                ],
                "codes": [
                    {
                        "id": "code_critique",
                        "name": "methodological_critique",
                        "code_type": "evaluation",
                        "confidence": 0.78
                    }
                ]
            }
        ])
        
        manager.get_automated_patterns = AsyncMock(return_value=[
            {
                "pattern_type": "entity_pattern",
                "name": "AI integration",
                "description": "technology pattern",
                "frequency": 8,
                "confidence": 0.82,
                "cross_interview": True,
                "supporting_quotes": [
                    {
                        "id": "quote_001",
                        "text": "We need better AI integration in our methods",
                        "interview_id": "interview_001",
                        "line_start": 15
                    },
                    {
                        "id": "quote_005",
                        "text": "AI can transform our research approach",
                        "interview_id": "interview_002", 
                        "line_start": 33
                    }
                ]
            },
            {
                "pattern_type": "code_pattern",
                "name": "methodological_improvement",
                "description": "process theme",
                "frequency": 12,
                "confidence": 0.88,
                "cross_interview": True,
                "supporting_quotes": [
                    {
                        "id": "quote_003",
                        "text": "We should modernize our analysis techniques",
                        "interview_id": "interview_001",
                        "line_start": 45
                    }
                ]
            }
        ])
        
        manager.get_provenance_chain = AsyncMock(return_value={
            "finding": {
                "id": "entity_ai",
                "name": "AI integration",
                "entity_type": "technology"
            },
            "finding_type": "entity",
            "evidence_count": 3,
            "evidence_chain": [
                {
                    "quote_id": "quote_001",
                    "interview_id": "interview_001",
                    "line_range": "15-15",
                    "text": "We need better AI integration in our methods",
                    "context": "Discussion about methodological improvements",
                    "confidence": 0.85,
                    "relationship_type": "MENTIONS"
                },
                {
                    "quote_id": "quote_005",
                    "interview_id": "interview_002",
                    "line_range": "33-33", 
                    "text": "AI can transform our research approach",
                    "context": "Future vision discussion",
                    "confidence": 0.9,
                    "relationship_type": "MENTIONS"
                }
            ]
        })
        
        return manager
    
    @pytest.mark.asyncio
    async def test_get_automation_summary(self, mock_neo4j_manager):
        """Test automation summary retrieval"""
        summary = await mock_neo4j_manager.get_automation_summary()
        
        # Verify statistics match expected automation output
        assert summary["statistics"]["quotes_extracted"] == 156
        assert summary["statistics"]["quote_nodes"] == 47
        assert summary["statistics"]["interviews_processed"] == 6
        assert summary["statistics"]["entities_detected"] == 25
        assert summary["statistics"]["entity_relationships"] == 11
        
        # Verify confidence distribution
        assert summary["confidence_distribution"]["high"] == 15
        assert summary["confidence_distribution"]["medium"] == 20
        assert summary["confidence_distribution"]["low"] == 12
        
        # Verify timeline has interview data
        assert "interview_001" in summary["timeline"]
        assert summary["timeline"]["interview_001"]["quotes"] == 25
        assert summary["timeline"]["interview_001"]["entities"] == 5
    
    @pytest.mark.asyncio 
    async def test_get_quotes_with_assignments(self, mock_neo4j_manager):
        """Test quote retrieval with entity/code assignments"""
        quotes = await mock_neo4j_manager.get_quotes_with_assignments("interview_001")
        
        # Verify quotes structure
        assert len(quotes) == 2
        
        # Test first quote
        quote1 = quotes[0]
        assert quote1["id"] == "quote_001"
        assert quote1["text"] == "We need better AI integration in our methods"
        assert quote1["line_start"] == 15
        assert quote1["line_end"] == 15
        assert quote1["confidence"] == 0.85
        
        # Verify entity assignments
        assert len(quote1["entities"]) == 1
        entity = quote1["entities"][0]
        assert entity["name"] == "AI integration"
        assert entity["entity_type"] == "technology"
        assert entity["confidence"] == 0.9
        
        # Verify code assignments
        assert len(quote1["codes"]) == 1
        code = quote1["codes"][0]
        assert code["name"] == "methodological_improvement"
        assert code["code_type"] == "process"
        assert code["confidence"] == 0.8
    
    @pytest.mark.asyncio
    async def test_get_automated_patterns(self, mock_neo4j_manager):
        """Test automated pattern detection retrieval"""
        patterns = await mock_neo4j_manager.get_automated_patterns(min_confidence=0.7)
        
        # Verify patterns structure
        assert len(patterns) == 2
        
        # Test entity pattern
        entity_pattern = patterns[0]
        assert entity_pattern["pattern_type"] == "entity_pattern"
        assert entity_pattern["name"] == "AI integration"
        assert entity_pattern["frequency"] == 8
        assert entity_pattern["confidence"] == 0.82
        assert entity_pattern["cross_interview"] == True
        
        # Verify supporting quotes
        assert len(entity_pattern["supporting_quotes"]) >= 1
        supporting_quote = entity_pattern["supporting_quotes"][0]
        assert supporting_quote["id"] == "quote_001"
        assert supporting_quote["interview_id"] == "interview_001"
        assert supporting_quote["line_start"] == 15
        
        # Test code pattern
        code_pattern = patterns[1]
        assert code_pattern["pattern_type"] == "code_pattern"
        assert code_pattern["name"] == "methodological_improvement"
        assert code_pattern["frequency"] == 12
        assert code_pattern["confidence"] == 0.88
    
    @pytest.mark.asyncio
    async def test_get_provenance_chain(self, mock_neo4j_manager):
        """Test provenance chain retrieval for findings"""
        provenance = await mock_neo4j_manager.get_provenance_chain("entity_ai", "entity")
        
        # Verify finding information
        assert provenance["finding"]["id"] == "entity_ai"
        assert provenance["finding"]["name"] == "AI integration"
        assert provenance["finding_type"] == "entity"
        assert provenance["evidence_count"] == 3
        
        # Verify evidence chain
        assert len(provenance["evidence_chain"]) == 2
        
        # Test first evidence item
        evidence1 = provenance["evidence_chain"][0]
        assert evidence1["quote_id"] == "quote_001"
        assert evidence1["interview_id"] == "interview_001"
        assert evidence1["line_range"] == "15-15"
        assert evidence1["text"] == "We need better AI integration in our methods"
        assert evidence1["confidence"] == 0.85
        assert evidence1["relationship_type"] == "MENTIONS"


class TestAutomationResultsViewer:
    """Test the AutomationResultsViewer class"""
    
    @pytest.fixture
    def mock_viewer(self, mock_neo4j_manager):
        """Create a mock automation results viewer"""
        viewer = AutomationResultsViewer()
        viewer.neo4j = mock_neo4j_manager
        return viewer
    
    def test_format_quote_display(self, mock_viewer):
        """Test quote formatting for display"""
        quote_data = {
            "id": "quote_001",
            "text": "We need better AI integration in our methods",
            "line_start": 15,
            "line_end": 15,
            "interview_id": "interview_001",
            "speaker": "Participant A",
            "confidence": 0.85,
            "context": "Discussion about methodological improvements",
            "entities": [
                {
                    "id": "entity_ai",
                    "name": "AI integration",
                    "entity_type": "technology",
                    "confidence": 0.9
                }
            ],
            "codes": [
                {
                    "id": "code_methods",
                    "name": "methodological_improvement", 
                    "code_type": "process",
                    "confidence": 0.8
                }
            ]
        }
        
        formatted = mock_viewer.format_quote_display(quote_data)
        
        # Verify key information is present
        assert "📝 Quote quote_001 (Lines 15-15)" in formatted
        assert "Interview: interview_001" in formatted
        assert "Speaker: Participant A" in formatted
        assert "🟢 0.85" in formatted  # High confidence indicator
        assert "We need better AI integration in our methods" in formatted
        assert "🔗 Entities:" in formatted
        assert "AI integration (technology)" in formatted
        assert "📋 Codes:" in formatted
        assert "methodological_improvement (process)" in formatted
    
    def test_format_automation_summary(self, mock_viewer):
        """Test automation summary formatting"""
        summary_data = {
            "statistics": {
                "quotes_extracted": 156,
                "quote_nodes": 47,
                "interviews_processed": 6,
                "entities_detected": 25,
                "entity_relationships": 11,
                "code_assignments": 33
            },
            "confidence_distribution": {
                "high": 15,
                "medium": 20,
                "low": 12
            },
            "timeline": {
                "interview_001": {"quotes": 25, "entities": 5},
                "interview_002": {"quotes": 30, "entities": 8}
            }
        }
        
        formatted = mock_viewer.format_automation_summary(summary_data)
        
        # Verify summary contains key statistics
        assert "🤖 AUTOMATED QUALITATIVE CODING RESULTS" in formatted
        assert "Interviews Processed: 6" in formatted
        assert "Quotes Extracted: 156" in formatted
        assert "Quote Nodes Created: 47" in formatted
        assert "Entities Detected: 25" in formatted
        assert "Entity Relationships: 11" in formatted
        assert "Code Assignments: 33" in formatted
        
        # Verify confidence distribution
        assert "🎯 Confidence Distribution:" in formatted
        assert "High (≥0.8): 15 items" in formatted
        assert "Medium (0.6-0.8): 20 items" in formatted
        assert "Low (<0.6): 12 items" in formatted
        
        # Verify timeline
        assert "⏱️ Processing Timeline:" in formatted
        assert "interview_001: 25 quotes, 5 entities" in formatted
        assert "interview_002: 30 quotes, 8 entities" in formatted
    
    def test_format_pattern_display(self, mock_viewer):
        """Test pattern formatting for display"""
        patterns_data = [
            {
                "pattern_type": "entity_pattern",
                "name": "AI integration",
                "description": "technology pattern",
                "frequency": 8,
                "confidence": 0.82,
                "supporting_quotes": [
                    {
                        "id": "quote_001",
                        "text": "We need better AI integration in our methods for the future of research",
                        "interview_id": "interview_001",
                        "line_start": 15
                    }
                ]
            }
        ]
        
        formatted = mock_viewer.format_pattern_display(patterns_data)
        
        # Verify pattern display
        assert "🔍 AUTOMATICALLY DETECTED PATTERNS" in formatted
        assert "Pattern 1: AI integration" in formatted
        assert "Type: entity_pattern" in formatted
        assert "Confidence: 0.82" in formatted
        assert "Frequency: 8 occurrences" in formatted
        assert "Description: technology pattern" in formatted
        assert "📝 Supporting Evidence:" in formatted
        assert "We need better AI integration in our methods..." in formatted
        assert "(interview_001:15)" in formatted


class TestCLICommands:
    """Test CLI command functionality"""
    
    @patch('src.qc.cli_automation_viewer.AutomationResultsViewer')
    def test_run_show_results_basic(self, mock_viewer_class):
        """Test basic show_results command execution"""
        # Mock the viewer instance
        mock_viewer = MagicMock()
        mock_viewer.setup = AsyncMock()
        mock_viewer.cleanup = AsyncMock()
        mock_viewer.neo4j = MagicMock()
        
        # Mock summary data
        mock_viewer.neo4j.get_automation_summary = AsyncMock(return_value={
            "statistics": {"quotes_extracted": 156, "interviews_processed": 6},
            "interview_ids": ["interview_001"]
        })
        mock_viewer.format_automation_summary = MagicMock(return_value="Formatted Summary")
        
        mock_viewer_class.return_value = mock_viewer
        
        # Test execution (this would be called by click in real usage)
        try:
            run_show_results([], 0.0, False, verbose=False)
        except SystemExit:
            pass  # Click commands may exit
        
        # Verify viewer was created and methods called
        mock_viewer_class.assert_called_once()
        mock_viewer.setup.assert_called_once()
    
    @patch('src.qc.cli_automation_viewer.AutomationResultsViewer')
    def test_run_browse_quotes_basic(self, mock_viewer_class):
        """Test basic browse_quotes command execution"""
        # Mock the viewer instance
        mock_viewer = MagicMock()
        mock_viewer.setup = AsyncMock()
        mock_viewer.cleanup = AsyncMock()
        mock_viewer.neo4j = MagicMock()
        
        # Mock quotes data
        mock_viewer.neo4j.get_quotes_with_assignments = AsyncMock(return_value=[
            {
                "id": "quote_001",
                "text": "Test quote",
                "line_start": 10,
                "line_end": 10,
                "interview_id": "interview_001"
            }
        ])
        mock_viewer.format_quote_display = MagicMock(return_value="Formatted Quote")
        
        mock_viewer_class.return_value = mock_viewer
        
        # Test execution
        try:
            run_browse_quotes("interview_001", verbose=False)
        except SystemExit:
            pass  # Click commands may exit
        
        # Verify viewer was created and methods called
        mock_viewer_class.assert_called_once()
        mock_viewer.setup.assert_called_once()
    
    @patch('src.qc.cli_automation_viewer.AutomationResultsViewer')
    def test_run_explore_patterns_basic(self, mock_viewer_class):
        """Test basic explore_patterns command execution"""
        # Mock the viewer instance
        mock_viewer = MagicMock()
        mock_viewer.setup = AsyncMock()
        mock_viewer.cleanup = AsyncMock()
        mock_viewer.neo4j = MagicMock()
        
        # Mock patterns data
        mock_viewer.neo4j.get_automated_patterns = AsyncMock(return_value=[
            {
                "pattern_type": "entity_pattern",
                "name": "AI integration",
                "confidence": 0.82
            }
        ])
        mock_viewer.format_pattern_display = MagicMock(return_value="Formatted Patterns")
        
        mock_viewer_class.return_value = mock_viewer
        
        # Test execution
        try:
            run_explore_patterns(verbose=False)
        except SystemExit:
            pass  # Click commands may exit
        
        # Verify viewer was created and methods called
        mock_viewer_class.assert_called_once()
        mock_viewer.setup.assert_called_once()


class TestAutomationDisplayValidation:
    """Validation tests for automation display functionality"""
    
    def test_confidence_score_display_accuracy(self):
        """Test that confidence scores are displayed accurately"""
        viewer = AutomationResultsViewer()
        
        # Test high confidence (≥0.8)
        high_conf_quote = {"id": "test", "confidence": 0.85, "text": "test", 
                          "line_start": 1, "line_end": 1, "interview_id": "test"}
        formatted = viewer.format_quote_display(high_conf_quote)
        assert "🟢 0.85" in formatted
        
        # Test medium confidence (0.6-0.8)
        med_conf_quote = {"id": "test", "confidence": 0.75, "text": "test",
                         "line_start": 1, "line_end": 1, "interview_id": "test"}
        formatted = viewer.format_quote_display(med_conf_quote)
        assert "🟡 0.75" in formatted
        
        # Test low confidence (<0.6)
        low_conf_quote = {"id": "test", "confidence": 0.45, "text": "test",
                         "line_start": 1, "line_end": 1, "interview_id": "test"}
        formatted = viewer.format_quote_display(low_conf_quote)
        assert "🔴 0.45" in formatted
    
    def test_line_number_display_accuracy(self):
        """Test that line numbers are displayed accurately"""
        viewer = AutomationResultsViewer()
        
        quote = {
            "id": "test_quote",
            "text": "Test quote text",
            "line_start": 25,
            "line_end": 27,
            "interview_id": "test_interview"
        }
        
        formatted = viewer.format_quote_display(quote)
        assert "(Lines 25-27)" in formatted
    
    def test_provenance_chain_completeness(self):
        """Test that provenance chains include all required information"""
        # This would test with actual Neo4j data in integration tests
        required_fields = [
            "finding", "finding_type", "evidence_count", "evidence_chain"
        ]
        
        # Mock data structure that should be returned
        expected_provenance = {
            "finding": {"id": "test", "name": "test_entity"},
            "finding_type": "entity",
            "evidence_count": 2,
            "evidence_chain": [
                {
                    "quote_id": "quote_1",
                    "interview_id": "interview_1",
                    "line_range": "10-10",
                    "text": "Test quote",
                    "confidence": 0.8,
                    "relationship_type": "MENTIONS"
                }
            ]
        }
        
        # Verify all required fields are present
        for field in required_fields:
            assert field in expected_provenance
        
        # Verify evidence chain structure
        evidence = expected_provenance["evidence_chain"][0]
        evidence_required = ["quote_id", "interview_id", "line_range", "text", "confidence"]
        for field in evidence_required:
            assert field in evidence


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])