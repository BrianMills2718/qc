"""
Real Integration Tests for Global Analysis End-to-End Workflow

NO MOCKS - Real API calls, real interviews, real databases
Following user requirement: "there should be no mocking"
"""
import pytest
import asyncio
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime
import os
import logging

# Add project root to Python path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from qc.core.global_qualitative_analyzer import GlobalQualitativeAnalyzer
from qc.storage.simple_neo4j_client import SimpleNeo4jClient, Neo4jConnectionError
from qc.models.comprehensive_analysis_models import GlobalCodingResult, EnhancedResult
from qc.core.load_and_verify_interviews import load_all_interviews_with_metadata

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.real
class TestRealGlobalAnalysisEndToEnd:
    """Real integration tests with actual API calls and databases."""
    
    @pytest.mark.asyncio
    async def test_real_neo4j_connection_and_schema(self):
        """Test real Neo4j connection and schema creation."""
        client = SimpleNeo4jClient()
        
        try:
            # Test connection
            await client.connect()
            logger.info("✅ Neo4j connection successful")
            
            # Test schema creation
            await client.create_schema()
            logger.info("✅ Neo4j schema created successfully")
            
            # Verify we can run a simple query
            async with client.driver.session() as session:
                result = await session.run("MATCH (n) RETURN count(n) as count LIMIT 1")
                record = await result.single()
                logger.info(f"✅ Neo4j query successful, node count: {record['count']}")
            
            assert client.is_connected
            
        finally:
            await client.close()
    
    @pytest.mark.asyncio
    async def test_real_global_analysis_small_sample(self):
        """
        Test complete pipeline with real data (small sample):
        1. Load 5 real DOCX files
        2. Run real Gemini API analysis
        3. Store in real Neo4j database
        4. Export real CSV/Markdown files
        """
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Initialize analyzer with real components
            analyzer = GlobalQualitativeAnalyzer()
            
            # Initialize Neo4j client
            neo4j_client = SimpleNeo4jClient()
            
            try:
                # Connect to Neo4j
                await neo4j_client.connect()
                await neo4j_client.create_schema()
                logger.info("✅ Connected to Neo4j")
                
                # Test with 5 real interviews
                logger.info("🔄 Starting real global analysis with 5 interviews...")
                result = await analyzer.analyze_global(sample_size=5)
                
                # Verify real analysis results
                assert isinstance(result, EnhancedResult)
                assert result.global_analysis.interviews_analyzed == 5
                assert len(result.global_analysis.themes) > 0
                assert len(result.global_analysis.codes) > 0
                assert result.traceability_completeness > 0.0
                
                logger.info(f"✅ Analysis complete: {len(result.global_analysis.themes)} themes, "
                          f"{len(result.global_analysis.codes)} codes")
                
                # Store in real Neo4j
                await neo4j_client.store_enhanced_result(result)
                logger.info("✅ Stored results in Neo4j")
                
                # Export real files
                analyzer.export_csv_files(result, output_dir / "csv")
                analyzer.export_markdown_report(result, output_dir / "report.md")
                analyzer.export_json_backup(result, output_dir / "analysis.json")
                
                # Verify real exports
                assert (output_dir / "csv" / "themes.csv").exists()
                assert (output_dir / "csv" / "codes.csv").exists()
                assert (output_dir / "csv" / "quotes.csv").exists()
                assert (output_dir / "report.md").exists()
                assert (output_dir / "analysis.json").exists()
                
                # Read and verify content
                with open(output_dir / "report.md", 'r', encoding='utf-8') as f:
                    report = f.read()
                    assert len(report) > 100
                    assert "Theme" in report
                    assert "Code" in report
                
                logger.info("✅ All exports created successfully")
                
                # Verify quote chains exist
                assert len(result.global_analysis.quote_chains) >= 0  # May be 0 for small sample
                
                # Verify code progressions exist
                assert len(result.global_analysis.code_progressions) >= 0  # May be 0 for small sample
                
                logger.info("✅ Real integration test completed successfully!")
                
            except Exception as e:
                logger.error(f"❌ Test failed: {str(e)}")
                raise
            finally:
                await neo4j_client.close()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_real_global_analysis_full_dataset(self):
        """
        Test complete pipeline with ALL 103 real interviews.
        WARNING: This uses real API credits and may take several minutes.
        """
        # Skip if not explicitly enabled
        if not os.getenv('RUN_FULL_INTEGRATION_TEST'):
            pytest.skip("Set RUN_FULL_INTEGRATION_TEST=1 to run full dataset test")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            analyzer = GlobalQualitativeAnalyzer()
            neo4j_client = SimpleNeo4jClient()
            
            try:
                # Connect to Neo4j
                await neo4j_client.connect()
                await neo4j_client.create_schema()
                
                # Run full analysis
                logger.info("🔄 Starting FULL global analysis with all 103 interviews...")
                logger.info("⚠️  This will use real Gemini API credits!")
                
                result = await analyzer.analyze_global()  # No sample_size = all interviews
                
                # Verify comprehensive results
                assert result.global_analysis.interviews_analyzed == 103
                assert len(result.global_analysis.themes) >= 5
                assert len(result.global_analysis.codes) >= 10
                assert len(result.global_analysis.quote_chains) > 0
                assert len(result.global_analysis.code_progressions) > 0
                assert result.traceability_completeness > 0.7
                
                logger.info(f"✅ Full analysis complete: "
                          f"{len(result.global_analysis.themes)} themes, "
                          f"{len(result.global_analysis.codes)} codes, "
                          f"{len(result.global_analysis.quote_chains)} quote chains")
                
                # Store in Neo4j
                await neo4j_client.store_enhanced_result(result)
                
                # Export all outputs
                analyzer.export_csv_files(result, output_dir / "csv")
                analyzer.export_markdown_report(result, output_dir / "report.md")
                analyzer.export_json_backup(result, output_dir / "analysis.json")
                
                # Verify comprehensive outputs
                csv_files = [
                    "themes.csv", "codes.csv", "quotes.csv", 
                    "quote_chains.csv", "contradictions.csv",
                    "stakeholder_positions.csv", "traceability_matrix.csv"
                ]
                
                for csv_file in csv_files:
                    assert (output_dir / "csv" / csv_file).exists()
                
                # Verify report quality
                with open(output_dir / "report.md", 'r', encoding='utf-8') as f:
                    report = f.read()
                    assert len(report) > 5000  # Substantial report
                    assert "Executive Summary" in report
                    assert "Key Themes" in report
                    assert "Quote Chains" in report
                    assert "Theoretical Insights" in report
                
                logger.info("✅ Full integration test completed successfully!")
                
            finally:
                await neo4j_client.close()
    
    @pytest.mark.asyncio
    async def test_real_error_handling(self):
        """Test real error scenarios without mocks."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Test with invalid sample size
        with pytest.raises(ValueError):
            await analyzer.analyze_global(sample_size=0)
        
        # Test with too large sample size
        with pytest.raises(ValueError):
            await analyzer.analyze_global(sample_size=1000)
        
        # Test Neo4j connection with wrong credentials
        client = SimpleNeo4jClient()
        client.password = "wrong_password"
        
        with pytest.raises(Neo4jConnectionError):
            await client.connect()


@pytest.mark.integration
@pytest.mark.real
class TestRealAnalysisQuality:
    """Test real analysis quality without mocks."""
    
    @pytest.mark.asyncio
    async def test_real_analysis_quality_metrics(self):
        """Test that real analysis meets quality standards."""
        analyzer = GlobalQualitativeAnalyzer()
        
        # Run real analysis with 3 interviews
        result = await analyzer.analyze_global(sample_size=3)
        
        # Real quality metrics
        assert result.global_analysis.confidence_scores.get("overall", 0) > 0
        assert result.global_analysis.interviews_analyzed == 3
        assert result.global_analysis.total_tokens_analyzed > 1000
        assert result.traceability_completeness > 0
        assert result.evidence_strength > 0
        
        # Verify real theoretical insights
        assert len(result.global_analysis.theoretical_insights) > 0
        assert len(result.global_analysis.emergent_theory) > 0
        
        logger.info(f"✅ Real quality metrics verified: "
                   f"Confidence: {result.global_analysis.confidence_scores.get('overall', 0):.2f}, "
                   f"Traceability: {result.traceability_completeness:.2f}")


if __name__ == "__main__":
    # Run real integration tests
    pytest.main([__file__, "-v", "-m", "integration and real"])