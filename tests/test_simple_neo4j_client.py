"""
TDD Tests for Simple Neo4j Client

Following proper TDD methodology: RED -> GREEN -> REFACTOR

Day 3 Task 3.2: Test Neo4j connection and basic graph operations
"""
import pytest
import asyncio
from pathlib import Path
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from qc.storage.simple_neo4j_client import SimpleNeo4jClient, Neo4jConnectionError
from qc.models.comprehensive_analysis_models import GlobalCodingResult, EnhancedResult


def create_mock_driver_with_session():
    """Helper function to create properly mocked Neo4j driver with session."""
    mock_driver = AsyncMock()
    mock_session = AsyncMock()
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    mock_driver.session.return_value = mock_session_context
    mock_driver.verify_connectivity = AsyncMock()
    return mock_driver, mock_session


class TestNeo4jClientInitialization:
    """Test Neo4j client initialization and connection."""
    
    def test_client_init_with_default_connection(self):
        """Test initializing client with default bolt connection."""
        # RED: This will fail because SimpleNeo4jClient doesn't exist yet
        client = SimpleNeo4jClient()
        
        assert client.uri == "bolt://localhost:7687"
        assert client.username == "neo4j"
        assert client.password is not None
        assert client.driver is None  # Not connected yet
    
    def test_client_init_with_custom_connection(self):
        """Test initializing client with custom connection parameters."""
        # RED: This will fail because SimpleNeo4jClient doesn't exist yet
        client = SimpleNeo4jClient(
            uri="bolt://localhost:7688",
            username="testuser",
            password="testpass"
        )
        
        assert client.uri == "bolt://localhost:7688"
        assert client.username == "testuser"
        assert client.password == "testpass"
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')
    async def test_connection_establishment(self, mock_driver_class):
        """Test establishing connection to Neo4j."""
        # Mock the Neo4j driver to avoid needing real database
        mock_driver = AsyncMock()
        mock_driver.verify_connectivity = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        
        # This should establish connection
        await client.connect()
        
        assert client.driver is not None
        assert client.is_connected is True
        mock_driver.verify_connectivity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_failure_handling(self):
        """Test handling connection failures gracefully."""
        # RED: This will fail because Neo4jConnectionError doesn't exist yet
        client = SimpleNeo4jClient(uri="bolt://invalid:7687")
        
        with pytest.raises(Neo4jConnectionError):
            await client.connect()
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')
    async def test_connection_cleanup(self, mock_driver_class):
        """Test proper connection cleanup."""
        mock_driver = AsyncMock()
        mock_driver.verify_connectivity = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        await client.connect()
        
        await client.close()
        
        assert client.is_connected is False
        assert client.driver is None
        mock_driver.close.assert_called_once()


class TestNeo4jSchemaCreation:
    """Test Neo4j graph schema creation for qualitative coding."""
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')
    async def test_create_basic_schema(self, mock_driver_class):
        """Test creating basic schema for interviews, codes, themes."""
        mock_driver, mock_session = create_mock_driver_with_session()
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        await client.connect()
        
        # Should create indexes and constraints
        await client.create_schema()
        
        # Verify schema creation calls were made
        assert mock_session.run.call_count > 0
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')  
    async def test_create_relationships_schema(self, mock_driver_class):
        """Test creating relationship types for qualitative coding."""
        mock_driver, mock_session = create_mock_driver_with_session()
        
        # Mock schema info results
        async def mock_run_side_effect(query):
            mock_result = AsyncMock()
            if "db.labels()" in query:
                mock_result.__aiter__.return_value = [
                    {"label": "Interview"}, {"label": "Code"}, {"label": "Theme"}, 
                    {"label": "Category"}, {"label": "Quote"}
                ]
            elif "db.relationshipTypes()" in query:
                mock_result.__aiter__.return_value = [
                    {"relationshipType": "CONTAINS_CODE"}, {"relationshipType": "BELONGS_TO_THEME"},
                    {"relationshipType": "HAS_QUOTE"}, {"relationshipType": "PART_OF_CHAIN"}
                ]
            return mock_result
        
        mock_session.run.side_effect = mock_run_side_effect
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        await client.connect()
        await client.create_schema()
        
        schema_info = await client.get_schema_info()
        
        assert "Interview" in schema_info["node_labels"]
        assert "Code" in schema_info["node_labels"] 
        assert "Theme" in schema_info["node_labels"]
        assert "CONTAINS_CODE" in schema_info["relationship_types"]


class TestNeo4jDataStorage:
    """Test storing qualitative coding results in Neo4j."""
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')
    async def test_store_global_coding_result(self, mock_driver_class):
        """Test storing GlobalCodingResult in Neo4j graph."""
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_tx = AsyncMock()
        mock_result = AsyncMock()
        mock_record = AsyncMock()
        
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        mock_session.begin_transaction.return_value.__aenter__.return_value = mock_tx
        mock_tx.run.return_value = mock_result
        mock_result.single.return_value = mock_record
        mock_record.__getitem__.return_value = "test_study_001"  # simulate record['study_id']
        mock_driver.verify_connectivity = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        await client.connect()
        
        # Create test result
        test_result = GlobalCodingResult(
            study_id="test_study_001",
            analysis_timestamp=datetime.now(),
            research_question="Test question",
            interviews_analyzed=5,
            total_tokens_analyzed=50000,
            themes=[],
            codes=[],
            categories=[],
            quote_chains=[],
            code_progressions=[],
            contradictions=[],
            stakeholder_mapping={},
            saturation_assessment={
                "saturation_point": "INT_003",
                "interview_number": 3,
                "evidence": "Test evidence",
                "new_codes_curve": [3, 2, 1],
                "new_themes_curve": [2, 1, 0],
                "stabilization_indicators": ["Pattern repetition"],
                "post_saturation_validation": "Test validation"
            },
            theoretical_insights=["Test insight"],
            emergent_theory="Test theory",
            methodological_notes="Test notes",
            processing_metadata={"test": "metadata"},
            confidence_scores={"overall": 0.8}
        )
        
        # Store in Neo4j
        result_id = await client.store_global_result(test_result)
        
        assert result_id is not None
        assert isinstance(result_id, str)
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')
    async def test_store_enhanced_result(self, mock_driver_class):
        """Test storing EnhancedResult with full traceability."""
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_tx = AsyncMock()
        mock_result = AsyncMock()
        mock_record = AsyncMock()
        
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        mock_session.begin_transaction.return_value.__aenter__.return_value = mock_tx
        mock_tx.run.return_value = mock_result
        mock_result.single.return_value = mock_record
        mock_record.__getitem__.return_value = "test_enhanced"
        mock_driver.verify_connectivity = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        await client.connect()
        
        # Create minimal enhanced result for testing
        global_result = GlobalCodingResult(
            study_id="test_enhanced",
            analysis_timestamp=datetime.now(),
            research_question="Test question",
            interviews_analyzed=3,
            total_tokens_analyzed=30000,
            themes=[],
            codes=[],
            categories=[],
            quote_chains=[],
            code_progressions=[],
            contradictions=[],
            stakeholder_mapping={},
            saturation_assessment={
                "saturation_point": "INT_002",
                "interview_number": 2,
                "evidence": "Test evidence",
                "new_codes_curve": [2, 1],
                "new_themes_curve": [1, 0],
                "stabilization_indicators": ["Stability"],
                "post_saturation_validation": "Validated"
            },
            theoretical_insights=["Insight"],
            emergent_theory="Theory",
            methodological_notes="Notes",
            processing_metadata={"test": "data"},
            confidence_scores={"overall": 0.9}
        )
        
        enhanced_result = EnhancedResult(
            global_analysis=global_result,
            csv_export_data={
                "themes_table": [],
                "codes_table": [],
                "quotes_table": [],
                "quote_chains_table": [],
                "contradictions_table": [],
                "stakeholder_positions_table": [],
                "saturation_curve_table": [],
                "traceability_matrix": []
            },
            markdown_report="# Test Report",
            executive_summary="Test Summary",
            complete_quote_inventory=[],
            interview_summaries={},
            traceability_completeness=0.95,
            quote_chain_coverage=0.85,
            stakeholder_coverage=0.80,
            evidence_strength=0.90
        )
        
        # Store enhanced result
        result_id = await client.store_enhanced_result(enhanced_result)
        
        assert result_id is not None
        assert isinstance(result_id, str)


class TestNeo4jQueries:
    """Test querying stored data from Neo4j."""
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')
    async def test_query_themes_by_prevalence(self, mock_driver_class):
        """Test querying themes ordered by prevalence."""
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.__aiter__.return_value = [
            {"theme_id": "T1", "name": "Theme 1", "prevalence": 0.8},
            {"theme_id": "T2", "name": "Theme 2", "prevalence": 0.6}
        ]
        mock_driver.verify_connectivity = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        await client.connect()
        
        themes = await client.get_themes_by_prevalence(min_prevalence=0.5)
        
        assert isinstance(themes, list)
        assert len(themes) == 2
        for theme in themes:
            assert "theme_id" in theme
            assert "name" in theme
            assert "prevalence" in theme
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')
    async def test_query_quote_chains(self, mock_driver_class):
        """Test querying quote chains for a theme."""
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.__aiter__.return_value = [
            {"chain_id": "CH1", "chain_type": "evolution", "quotes_sequence": ["Q1", "Q2"]}
        ]
        mock_driver.verify_connectivity = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        await client.connect()
        
        chains = await client.get_quote_chains_for_theme("THEME_001")
        
        assert isinstance(chains, list)
        assert len(chains) == 1
        assert "chain_id" in chains[0]
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')
    async def test_query_code_progressions(self, mock_driver_class):
        """Test querying how codes evolved across interviews."""
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_record = AsyncMock()
        
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.single.return_value = mock_record
        mock_record.__iter__.side_effect = lambda: iter([("code_id", "CODE_001"), ("progression_type", "evolving"), ("timeline", [])])
        mock_driver.verify_connectivity = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        await client.connect()
        
        progressions = await client.get_code_progressions("CODE_001")
        
        assert isinstance(progressions, dict)
        assert "code_id" in progressions
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')
    async def test_query_contradictions(self, mock_driver_class):
        """Test querying contradictions with evidence."""
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.__aiter__.return_value = [
            {"contradiction_id": "C1", "position_a": "Pro", "position_b": "Con", "evidence_a": ["E1"], "evidence_b": ["E2"]}
        ]
        mock_driver.verify_connectivity = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        await client.connect()
        
        contradictions = await client.get_contradictions_for_theme("THEME_001")
        
        assert isinstance(contradictions, list)
        assert len(contradictions) == 1
        assert "contradiction_id" in contradictions[0]


class TestNeo4jErrorHandling:
    """Test error handling for Neo4j operations."""
    
    @pytest.mark.asyncio
    async def test_connection_retry_mechanism(self):
        """Test connection retry with exponential backoff."""
        client = SimpleNeo4jClient(uri="bolt://invalid:7687")
        
        # Should retry connection failures
        with pytest.raises(Neo4jConnectionError):
            await client.connect_with_retry(max_retries=3)
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')
    async def test_query_error_handling(self, mock_driver_class):
        """Test handling query failures gracefully."""
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        mock_session.run.side_effect = Exception("Query failed")
        mock_driver.verify_connectivity = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        await client.connect()
        
        # Should handle malformed queries
        with pytest.raises(Exception):
            await client.execute_query("INVALID CYPHER QUERY")
    
    @pytest.mark.asyncio
    @patch('qc.storage.simple_neo4j_client.AsyncGraphDatabase.driver')
    async def test_transaction_rollback(self, mock_driver_class):
        """Test transaction rollback on errors."""
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_tx = AsyncMock()
        
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        mock_session.begin_transaction.return_value = mock_tx
        mock_tx.__aenter__.return_value = mock_tx
        mock_tx.run.side_effect = [None, Exception("Invalid query")]  # First succeeds, second fails
        mock_driver.verify_connectivity = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        client = SimpleNeo4jClient()
        await client.connect()
        
        # Should rollback failed transactions
        with pytest.raises(Exception):
            async with client.transaction() as tx:
                await tx.run("CREATE (n:Test)")
                await tx.run("INVALID QUERY")  # This should cause rollback


if __name__ == "__main__":
    # Run tests to see failures (RED phase)
    pytest.main([__file__, "-v"])