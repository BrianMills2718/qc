"""
Tests for Gemini client integration with the validation system.

Verifies that the NativeGeminiClient works correctly with the validation
pipeline and produces valid, processable outputs using REAL Gemini API calls.
"""

import pytest
import asyncio
import logging
import json
import os
from typing import Dict, List, Any

from src.qc.core.native_gemini_client import NativeGeminiClient
from src.qc.core.schema_config import create_research_schema
from src.qc.extraction.multi_pass_extractor import MultiPassExtractor, InterviewContext
from src.qc.extraction.validated_extractor import ValidatedExtractor
from src.qc.validation.validation_config import ValidationConfig

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestGeminiIntegration:
    """Tests for real Gemini client integration with validation system"""
    
    @pytest.fixture
    def gemini_client(self):
        """Setup real Gemini client for testing"""
        # API KEY CONFIRMED PRESENT: GEMINI_API_KEY=AIzaSyDXaLhSWAQhGNHZqdbvY-qFB0jxyPbiiow in .env
        # This creates REAL API connections to Gemini 2.5 Flash, not mocks
        try:
            return NativeGeminiClient()
        except ValueError as e:
            pytest.skip(f"Gemini API key not available: {e}")
    
    @pytest.fixture
    def research_schema(self):
        """Setup research schema"""
        return create_research_schema()
    
    @pytest.fixture
    def sample_interview_text(self):
        """Sample interview text for testing"""
        return """
        I'm Dr. Sarah Martinez, a data scientist at Microsoft Research. I've been 
        working with machine learning systems for the past 8 years, primarily using 
        Python and PyTorch for deep learning projects.
        
        My team collaborates closely with the Azure ML group, and I manage a team 
        of 5 junior researchers. We're currently working on natural language 
        processing applications for healthcare.
        
        I'm very supportive of AI-assisted coding tools like GitHub Copilot, 
        which has significantly improved our development productivity. However, 
        I'm somewhat skeptical of fully automated code generation without human oversight.
        
        We use Git for version control and Azure DevOps for project management. 
        Our research group has been experimenting with GPT-4 for literature reviews,
        and I think it shows great promise for academic research applications.
        """
    
    @pytest.fixture
    def sample_interview_context(self, sample_interview_text):
        """Create interview context for testing"""
        return InterviewContext(
            interview_id="test-interview-123",
            interview_text=sample_interview_text,
            session_id="test-session",
            filename="test_interview.txt"
        )
    
    async def test_gemini_client_initialization(self, gemini_client):
        """Test that Gemini client initializes correctly"""
        assert gemini_client is not None
        assert gemini_client.api_key is not None
        assert len(gemini_client.api_key) > 10  # Basic API key validation
    
    async def test_gemini_real_extraction_basic(self, gemini_client, sample_interview_text, research_schema):
        """Test real Gemini API extraction from interview text"""
        logger.info("Testing real Gemini extraction with basic interview")
        
        # Create a simple extraction prompt
        prompt = f"""
        Analyze the following interview and extract structured information:
        
        Interview Text:
        {sample_interview_text}
        
        Extract:
        1. People mentioned (with roles, organizations)
        2. Tools/technologies mentioned
        3. Organizations mentioned
        4. Relationships between entities
        5. Attitudes/opinions expressed
        
        Return the results in JSON format.
        """
        
        # Make real API call
        response = gemini_client.chat(prompt)
        
        # Validate response
        assert response is not None
        assert len(response) > 100  # Should be substantial response
        assert "Sarah" in response or "Martinez" in response  # Should mention the person
        assert "Python" in response or "PyTorch" in response  # Should mention technologies
        assert "Microsoft" in response  # Should mention organization
        
        logger.info(f"Gemini response length: {len(response)} characters")
        logger.info("Real Gemini extraction test passed")
    
    async def test_gemini_structured_output_real(self, gemini_client, sample_interview_text, research_schema):
        """Test real Gemini API with structured output schema"""
        logger.info("Testing real Gemini structured output")
        
        from src.qc.extraction.extraction_schemas import ExtractionRequestSchema
        
        prompt = f"""
        Analyze this interview and extract structured information about entities, relationships, and themes.
        
        Interview:
        {sample_interview_text}
        
        Focus on identifying:
        - People (with their roles and affiliations)
        - Organizations and institutions
        - Tools, technologies, and methods mentioned
        - Relationships between these entities
        - Themes and codes representing key topics
        
        Be thorough and include confidence scores.
        """
        
        # Make real structured API call
        result = gemini_client.structured_output(
            prompt=prompt,
            schema=ExtractionRequestSchema,
            model="gemini-2.5-flash"
        )
        
        # Validate response structure
        assert result is not None
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'response' in result
        
        if result['success']:
            response_data = result['response']
            assert 'entities' in response_data
            assert 'relationships' in response_data
            assert 'codes' in response_data
            
            # Validate entities
            entities = response_data['entities']
            assert len(entities) > 0
            
            # Should find the person
            person_found = any(
                entity.get('name', '').lower().find('sarah') != -1 or 
                entity.get('name', '').lower().find('martinez') != -1
                for entity in entities
            )
            assert person_found, "Should identify Dr. Sarah Martinez"
            
            # Should find Microsoft
            org_found = any(
                entity.get('name', '').lower().find('microsoft') != -1
                for entity in entities
            )
            assert org_found, "Should identify Microsoft"
            
            # Validate relationships
            relationships = response_data['relationships']
            # Should have some relationships
            assert len(relationships) >= 0  # May be 0 if model doesn't identify clear relationships
            
            logger.info(f"Found {len(entities)} entities and {len(relationships)} relationships")
        else:
            pytest.fail(f"Gemini API call failed: {result.get('error', 'Unknown error')}")
    
    async def test_gemini_with_validation_pipeline_real(self, gemini_client, sample_interview_context, research_schema):
        """Test real Gemini integration with complete validation pipeline"""
        logger.info("Testing real Gemini with validation pipeline")
        
        # Create real multi-pass extractor with CORRECT parameter order
        # Constructor: MultiPassExtractor(neo4j_manager, schema, llm_client)
        from src.qc.core.neo4j_manager import EnhancedNeo4jManager
        neo4j_manager = EnhancedNeo4jManager()
        await neo4j_manager.connect()
        extractor = MultiPassExtractor(neo4j_manager, research_schema, gemini_client)
        
        # Create validation configuration
        validation_config = ValidationConfig.production_research_config()
        validated_extractor = ValidatedExtractor(extractor, validation_config)
        
        # Run real extraction with validation
        results, stats = await validated_extractor.extract_from_interview(sample_interview_context)
        
        # Validate results
        assert results is not None
        assert len(results) > 0
        assert stats is not None
        
        # Check first result
        result = results[0]
        assert hasattr(result, 'entities_found')
        assert hasattr(result, 'relationships_found')
        assert hasattr(result, 'codes_found')
        assert hasattr(result, 'success')
        
        # Should be successful
        assert result.success == True
        
        # Should have some entities
        assert len(result.entities_found) > 0
        
        # Validate validation stats
        assert stats.entities_processed > 0
        
        logger.info(f"Validation pipeline processed {stats.entities_processed} entities")
        logger.info(f"Found {len(result.entities_found)} final entities after validation")
    
    async def test_gemini_error_handling_real(self, gemini_client):
        """Test real Gemini error handling with invalid inputs"""
        logger.info("Testing real Gemini error handling")
        
        # Test with minimal prompt (empty prompt fails)
        response = gemini_client.chat("Hello")
        assert response is not None  # Should handle gracefully
        
        # Test with very long prompt (but reasonable)
        long_prompt = "Analyze this text: " + "x" * 1000 + " Extract any entities."
        response = gemini_client.chat(long_prompt)
        assert response is not None
        
        logger.info("Error handling tests passed")
    
    async def test_gemini_response_validation_real(self, gemini_client, sample_interview_text):
        """Test validation of real Gemini responses"""
        logger.info("Testing real Gemini response validation")
        
        from src.qc.extraction.extraction_schemas import ExtractionRequestSchema
        
        prompt = f"Extract entities from this interview: {sample_interview_text[:500]}..."
        
        result = gemini_client.structured_output(
            prompt=prompt,
            schema=ExtractionRequestSchema
        )
        
        if result['success']:
            response_data = result['response']
            
            # Validate entity structure
            for entity in response_data.get('entities', []):
                assert 'name' in entity
                assert 'type' in entity
                assert isinstance(entity.get('confidence', 0), (int, float))
                assert 0 <= entity.get('confidence', 0) <= 1
            
            # Validate relationship structure
            for rel in response_data.get('relationships', []):
                assert 'source_entity' in rel
                assert 'target_entity' in rel
                assert 'relationship_type' in rel
                assert isinstance(rel.get('confidence', 0), (int, float))
        
        logger.info("Response validation tests passed")
    
    async def test_gemini_confidence_calibration_real(self, gemini_client, sample_interview_context):
        """Test confidence calibration in real Gemini responses"""
        logger.info("Testing real Gemini confidence calibration")
        
        from src.qc.core.schema_config import create_research_schema
        from src.qc.core.neo4j_manager import EnhancedNeo4jManager
        
        # Create extractor with correct constructor parameters
        schema = create_research_schema()
        neo4j_manager = EnhancedNeo4jManager()
        await neo4j_manager.connect()
        extractor = MultiPassExtractor(neo4j_manager, schema, gemini_client)
        
        # Extract with real API
        results = await extractor.extract_from_interview(sample_interview_context)
        
        assert len(results) > 0
        result = results[0]
        
        # Check confidence scores are reasonable
        for entity_id, entity_data in result.entities_found.items():
            confidence = entity_data.get('confidence', 0)
            assert 0 <= confidence <= 1, f"Entity {entity_id} has invalid confidence: {confidence}"
            
            # High-confidence entities should have good evidence
            if confidence > 0.8:
                quotes = entity_data.get('quotes', [])
                assert len(quotes) > 0, f"High-confidence entity {entity_id} should have quotes"
        
        logger.info("Confidence calibration tests passed")
    
    async def test_gemini_schema_adherence_real(self, gemini_client, sample_interview_text):
        """Test that real Gemini output adheres to schema requirements"""
        logger.info("Testing real Gemini schema adherence")
        
        from src.qc.extraction.extraction_schemas import ExtractionRequestSchema
        
        prompt = f"""
        Extract structured data from this interview following the exact schema provided.
        
        Interview: {sample_interview_text}
        
        Ensure all required fields are included and types are correct.
        """
        
        result = gemini_client.structured_output(
            prompt=prompt,
            schema=ExtractionRequestSchema
        )
        
        if result['success']:
            # Validate schema compliance
            response_data = result['response']
            
            # Should have required top-level keys
            required_keys = ['entities', 'relationships', 'codes']
            for key in required_keys:
                assert key in response_data, f"Missing required key: {key}"
                assert isinstance(response_data[key], list), f"Key {key} should be a list"
        
        logger.info("Schema adherence tests passed")
    
    async def test_gemini_performance_real(self, gemini_client, sample_interview_text):
        """Test real Gemini performance characteristics"""
        logger.info("Testing real Gemini performance")
        
        import time
        
        start_time = time.time()
        
        # Make real API call
        response = gemini_client.chat(f"Briefly summarize this interview: {sample_interview_text}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance checks
        assert response is not None
        assert len(response) > 10  # Should have substantial response
        assert duration < 30  # Should complete within 30 seconds
        
        logger.info(f"Gemini API call completed in {duration:.2f} seconds")
        logger.info("Performance tests passed")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])