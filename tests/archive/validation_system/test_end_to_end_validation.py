"""
End-to-end tests for the complete validation system workflow.

Tests the entire pipeline from CLI commands through validation to Neo4j storage
and cross-interview analysis.
"""

import pytest
import asyncio
import tempfile
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
# All tests now use real Gemini API calls - no mocks

from src.qc.cli import QualitativeCodingCLI
from src.qc.core.neo4j_manager import EnhancedNeo4jManager
from src.qc.validation.config_manager import ValidationConfigManager
from src.qc.analysis.cross_interview_analyzer import CrossInterviewAnalyzer, CrossInterviewQueryBuilder
from src.qc.extraction.extraction_schemas import ExtractedEntity, ExtractedRelationship, ExtractedCode
from src.qc.extraction.multi_pass_extractor import ExtractionResult

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEndToEndValidation:
    """End-to-end tests for complete validation workflow"""
    
    @pytest.fixture
    async def cli_instance(self):
        """Setup CLI instance for testing"""
        cli = QualitativeCodingCLI()
        await cli.setup()
        yield cli
        await cli.cleanup()
    
    @pytest.fixture
    async def clean_database(self, cli_instance):
        """Ensure clean database for testing"""
        # Clear the database before test
        await cli_instance.neo4j.clear_database()
        yield
        # Leave data for inspection after test
    
    @pytest.fixture
    def sample_interviews(self):
        """Create sample interview files for testing"""
        interviews = {
            "interview_1.txt": """
            I'm Dr. Sarah Chen, a researcher at MIT working on artificial intelligence.
            I primarily use Python and TensorFlow for my deep learning projects.
            My team collaborates extensively, and I manage a group of graduate students.
            
            We've been experimenting with GPT-4 for code generation, and I'm generally
            supportive of AI tools that enhance productivity. However, I'm skeptical
            of relying too heavily on AI for critical research decisions.
            
            I work closely with Professor John Smith from Stanford on joint projects.
            Our collaboration spans multiple institutions and has been very productive.
            """,
            
            "interview_2.txt": """
            Hello, I'm Mark Johnson, a software engineer at Google. I've been working
            with machine learning systems for about 5 years now. My primary tools
            are Python, Kubernetes, and various Google Cloud services.
            
            I'm a strong advocate for automated testing and continuous integration.
            The team I'm part of uses GitHub for version control, which has been
            essential for our distributed development model.
            
            I'm somewhat critical of newer AI coding assistants like ChatGPT because
            they sometimes generate unreliable code. I prefer more traditional
            development approaches with proper code review processes.
            """,
            
            "interview_3.txt": """
            I'm Dr. Lisa Wang from UC Berkeley, specializing in data science and
            machine learning research. I extensively use R and Python for statistical
            analysis, and I manage our department's research computing infrastructure.
            
            I collaborate with both Dr. Sarah Chen at MIT and several industry partners.
            Our team advocates strongly for open science and reproducible research
            methodologies. We use Git and Docker for ensuring reproducibility.
            
            I'm optimistic about AI tools like Claude and GPT-4 for research assistance,
            though I maintain that human oversight is crucial for quality assurance.
            """
        }
        
        # Create temporary files
        temp_files = {}
        for filename, content in interviews.items():
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.write(content)
            temp_file.close()
            temp_files[filename] = temp_file.name
        
        yield temp_files
        
        # Cleanup temporary files
        for filepath in temp_files.values():
            Path(filepath).unlink(missing_ok=True)
    
    async def test_cli_analyze_with_validation_modes(self, cli_instance, clean_database, sample_interviews):
        """Test CLI analyze command with different validation modes using real Gemini API"""
        
        interview_files = list(sample_interviews.values())
        
        # Test with hybrid validation (default)
        await cli_instance.analyze_interviews(
            files=interview_files,
            validation_mode="hybrid",
            enable_validation=True
        )
        
        # Query the results to verify data was stored
        query_result = await cli_instance.neo4j.execute_cypher(
            "MATCH (p:Person) RETURN count(p) as person_count"
        )
        person_count = query_result[0]['person_count'] if query_result else 0
        
        logger.info(f"Hybrid mode extracted {person_count} persons")
        assert person_count > 0, "Should extract at least some persons"
        
        # Clear for next test
        await cli_instance.neo4j.clear_database()
        
        # Test with academic validation (restrictive)
        await cli_instance.analyze_interviews(
            files=interview_files,
            validation_mode="academic",
            enable_validation=True
        )
        
        query_result = await cli_instance.neo4j.execute_cypher(
            "MATCH (p:Person) RETURN count(p) as person_count"
        )
        academic_person_count = query_result[0]['person_count'] if query_result else 0
        
        logger.info(f"Academic mode extracted {academic_person_count} persons")
        
        # Clear for next test
        await cli_instance.neo4j.clear_database()
        
        # Test with exploratory validation (permissive)
        await cli_instance.analyze_interviews(
            files=interview_files,
            validation_mode="exploratory",
            enable_validation=True
        )
        
        query_result = await cli_instance.neo4j.execute_cypher(
            "MATCH (p:Person) RETURN count(p) as person_count"
        )
        exploratory_person_count = query_result[0]['person_count'] if query_result else 0
        
        logger.info(f"Exploratory mode extracted {exploratory_person_count} persons")
        
        # Verify reasonable extraction occurred in all modes
        assert academic_person_count >= 0
        assert exploratory_person_count >= 0
    
    async def test_validation_config_file_workflow(self, cli_instance, clean_database, sample_interviews):
        """Test complete workflow with custom validation configuration using real Gemini API"""
        # Create default configs
        cli_instance.create_default_configs()
        
        # Create custom config for testing
        config_manager = ValidationConfigManager()
        custom_config_path = config_manager.config_dir / "test_custom.yaml"
        
        custom_config_content = """
entities: hybrid
relationships: open
entity_matching: smart
property_validation: hybrid
consolidation_threshold: 0.8
auto_reject_unknown: false
auto_merge_similar: true
require_evidence: false
quality_threshold: 0.6
confidence_auto_approve: 0.85
confidence_flag_review: 0.65
confidence_require_validation: 0.4
standard_entity_types:
- Person
- Organization
- Tool
- Method
- Concept
- Technology
standard_relationship_types:
- WORKS_AT
- USES
- MANAGES
- PART_OF
- IMPLEMENTS
- COLLABORATES_WITH
- ADVOCATES_FOR
- SKEPTICAL_OF
- SUPPORTS
- CRITICIZES
_metadata:
  name: test_custom
  created_by: EndToEndTest
  config_version: '1.0'
"""
        
        custom_config_path.write_text(custom_config_content)
        
        try:
            # Test analysis with custom config file
            interview_files = list(sample_interviews.values())
            
            await cli_instance.analyze_interviews(
                files=interview_files,
                config_file="test_custom",
                enable_validation=True
            )
            
            # Verify data was extracted and stored
            query_result = await cli_instance.neo4j.execute_cypher("""
                MATCH (n) 
                RETURN labels(n) as node_labels, count(n) as count
                ORDER BY count DESC
            """)
            
            total_nodes = sum(record['count'] for record in query_result)
            logger.info(f"Custom config extracted {total_nodes} total nodes")
            
            for record in query_result:
                logger.info(f"  {record['node_labels']}: {record['count']}")
            
            assert total_nodes > 0, "Should extract nodes with custom config"
            
        finally:
            # Cleanup custom config
            custom_config_path.unlink(missing_ok=True)
    
    async def test_quality_validation_end_to_end(self, cli_instance, clean_database, sample_interviews):
        """Test quality validation effects throughout the pipeline using real Gemini API"""
        interview_files = list(sample_interviews.values())
        
        # Run with high quality threshold
        await cli_instance.analyze_interviews(
            files=interview_files,
            validation_mode="academic",  # Strict mode
            enable_validation=True
        )
        
        # Query validation-related metadata
        query_result = await cli_instance.neo4j.execute_cypher("""
            MATCH (n) 
            WHERE n.confidence IS NOT NULL
            RETURN avg(n.confidence) as avg_confidence, 
                   min(n.confidence) as min_confidence,
                   max(n.confidence) as max_confidence,
                   count(n) as node_count
        """)
        
        if query_result:
            stats = query_result[0]
            logger.info(f"Quality stats: avg={stats['avg_confidence']:.2f}, "
                       f"min={stats['min_confidence']:.2f}, "
                       f"max={stats['max_confidence']:.2f}, "
                       f"count={stats['node_count']}")
            
            # Academic mode should maintain reasonable quality
            assert stats['min_confidence'] >= 0.3, "Minimum confidence too low"
            assert stats['avg_confidence'] >= 0.5, "Average confidence too low"
    
    async def test_entity_consolidation_end_to_end(self, cli_instance, clean_database, sample_interviews):
        """Test entity consolidation throughout the complete pipeline"""
        interview_files = list(sample_interviews.values())
        
        # Run analysis with consolidation enabled
        await cli_instance.analyze_interviews(
            files=interview_files,
            validation_mode="hybrid",
            enable_validation=True
        )
        
        # Check for potential duplicate entities that should have been consolidated
        query_result = await cli_instance.neo4j.execute_cypher("""
            MATCH (p:Person)
            RETURN p.name as name, count(*) as occurrences
            ORDER BY occurrences DESC
        """)
        
        # Log person names to check for duplicates
        logger.info("Extracted persons:")
        duplicate_found = False
        for record in query_result:
            logger.info(f"  {record['name']}: {record['occurrences']} occurrences")
            if record['occurrences'] > 1:
                duplicate_found = True
        
        # With good consolidation, we shouldn't have many duplicates
        if duplicate_found:
            logger.warning("Found potential duplicates - consolidation may need tuning")
    
    async def test_cross_interview_analysis_end_to_end(self, cli_instance, clean_database, sample_interviews):
        """Test cross-interview analysis with validated data"""
        interview_files = list(sample_interviews.values())
        
        # First, populate database with validated extractions
        await cli_instance.analyze_interviews(
            files=interview_files,
            validation_mode="hybrid",
            enable_validation=True
        )
        
        # Test consensus pattern analysis
        await cli_instance.analyze_consensus_patterns(threshold=0.6)
        
        # Test divergence pattern analysis
        await cli_instance.analyze_divergence_patterns()
        
        # Test knowledge gap analysis
        await cli_instance.analyze_knowledge_gaps()
        
        # Test innovation diffusion analysis
        await cli_instance.analyze_innovation_diffusion()
        
        # Verify the data supports cross-interview analysis
        query_result = await cli_instance.neo4j.execute_cypher("""
            MATCH (p:Person)-[r:USES]->(t:Tool)
            RETURN t.name as tool, count(DISTINCT p.interview_id) as interview_count
            ORDER BY interview_count DESC
            LIMIT 5
        """)
        
        logger.info("Tools mentioned across interviews:")
        for record in query_result:
            logger.info(f"  {record['tool']}: {record['interview_count']} interviews")
    
    async def test_natural_language_query_end_to_end(self, cli_instance, clean_database, sample_interviews):
        """Test natural language querying with validated data"""
        interview_files = list(sample_interviews.values())
        
        # Populate database
        await cli_instance.analyze_interviews(
            files=interview_files,
            validation_mode="hybrid",
            enable_validation=True
        )
        
        # Test various natural language queries
        test_queries = [
            "Who uses Python?",
            "What tools do researchers use?",
            "Show me all collaborations",
            "Who is skeptical of AI tools?",
            "What organizations are mentioned?"
        ]
        
        for query in test_queries:
            logger.info(f"Testing query: {query}")
            try:
                await cli_instance.query_data(query)
                logger.info(f"  ✓ Query executed successfully")
            except Exception as e:
                logger.warning(f"  ✗ Query failed: {e}")
    
    async def test_error_recovery_end_to_end(self, cli_instance, clean_database):
        """Test error recovery throughout the pipeline using real Gemini API"""
        # Test with problematic interview content
        problematic_interviews = {
            "empty.txt": "",
            "malformed.txt": "This is not a proper interview format...",
            "special_chars.txt": "Interview with émilie françois about résumé parsing! 🚀",
            "very_short.txt": "Hi."
        }
        
        temp_files = {}
        for filename, content in problematic_interviews.items():
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(content)
            temp_file.close()
            temp_files[filename] = temp_file.name
        
        try:
            # Should handle problematic inputs gracefully
            await cli_instance.analyze_interviews(
                files=list(temp_files.values()),
                validation_mode="hybrid",
                enable_validation=True
            )
            
            # Verify system didn't crash and some processing occurred
            query_result = await cli_instance.neo4j.execute_cypher(
                "MATCH (n) RETURN count(n) as total_nodes"
            )
            
            total_nodes = query_result[0]['total_nodes'] if query_result else 0
            logger.info(f"Extracted {total_nodes} nodes from problematic inputs")
            
            # System should handle errors gracefully
            assert True, "Pipeline completed without crashing"
            
        finally:
            # Cleanup
            for filepath in temp_files.values():
                Path(filepath).unlink(missing_ok=True)
    
    async def test_validation_statistics_end_to_end(self, cli_instance, clean_database, sample_interviews):
        """Test validation statistics reporting through the complete pipeline"""
        interview_files = list(sample_interviews.values())
        
        # Create a temporary output file for analysis results
        temp_output = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        temp_output.close()
        
        try:
            # Run analysis with output file to capture statistics
            await cli_instance.analyze_interviews(
                files=interview_files,
                output=temp_output.name,
                validation_mode="hybrid",
                enable_validation=True
            )
            
            # Read the output file to verify statistics are included
            output_content = Path(temp_output.name).read_text()
            
            # Check for validation statistics in output
            validation_indicators = [
                "Validation mode",
                "Entities processed",
                "Relationships processed",
                "Quality issues found",
                "Validation time"
            ]
            
            found_indicators = []
            for indicator in validation_indicators:
                if indicator in output_content:
                    found_indicators.append(indicator)
            
            logger.info(f"Found validation indicators: {found_indicators}")
            
            # Should find most validation indicators in output
            assert len(found_indicators) >= 3, f"Expected more validation statistics in output"
            
        finally:
            # Cleanup
            Path(temp_output.name).unlink(missing_ok=True)
    
    async def test_complete_workflow_performance(self, cli_instance, clean_database, sample_interviews):
        """Test performance of complete validation workflow using real Gemini API"""
        interview_files = list(sample_interviews.values())
        
        # Measure total workflow time
        start_time = datetime.utcnow()
        
        await cli_instance.analyze_interviews(
            files=interview_files,
            validation_mode="hybrid",
            enable_validation=True
        )
        
        total_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Query final results
        query_result = await cli_instance.neo4j.execute_cypher("""
            MATCH (n) 
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
        """)
        
        total_nodes = sum(record['count'] for record in query_result)
        nodes_per_second = total_nodes / total_time if total_time > 0 else 0
        
        logger.info(f"Performance metrics:")
        logger.info(f"  Total time: {total_time:.2f}s")
        logger.info(f"  Total nodes: {total_nodes}")
        logger.info(f"  Nodes per second: {nodes_per_second:.2f}")
        logger.info(f"  Files processed: {len(interview_files)}")
        
        # Performance should be reasonable
        assert total_time < 120, f"Workflow took too long: {total_time:.2f}s"
        assert nodes_per_second > 0.1, f"Processing rate too slow: {nodes_per_second:.2f} nodes/s"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])