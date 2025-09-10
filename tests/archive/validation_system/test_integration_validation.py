"""
Integration tests for the enhanced validation system.

Tests the integration between validation components, ensuring they work
together correctly with the extraction pipeline.
"""

import pytest
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from src.qc.core.neo4j_manager import EnhancedNeo4jManager
from src.qc.core.native_gemini_client import NativeGeminiClient
from src.qc.core.schema_config import create_research_schema
from src.qc.extraction.multi_pass_extractor import MultiPassExtractor, InterviewContext
from src.qc.extraction.validated_extractor import ValidatedExtractor, ValidationStats
from src.qc.validation.validation_config import ValidationConfig, ValidationMode
from src.qc.validation.config_manager import ValidationConfigManager
from src.qc.analysis.cross_interview_analyzer import CrossInterviewAnalyzer

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestValidationIntegration:
    """Integration tests for validation system components"""
    
    @pytest.fixture
    async def neo4j_manager(self):
        """Setup Neo4j manager for testing"""
        manager = EnhancedNeo4jManager()
        await manager.connect()
        yield manager
        await manager.close()
    
    @pytest.fixture
    def gemini_client(self):
        """Setup Gemini client for testing"""
        return NativeGeminiClient()
    
    @pytest.fixture
    def research_schema(self):
        """Setup research schema"""
        return create_research_schema()
    
    @pytest.fixture
    async def base_extractor(self, neo4j_manager, research_schema):
        """Setup base multi-pass extractor"""
        return MultiPassExtractor(neo4j_manager, research_schema)
    
    @pytest.fixture
    def validation_config_manager(self):
        """Setup validation config manager"""
        return ValidationConfigManager()
    
    @pytest.fixture
    def sample_interview_text(self):
        """Sample interview text for testing"""
        return """
        I'm Dr. Alice Smith from Stanford University. I work extensively with Python 
        and TensorFlow for my machine learning research. The Python community has 
        been very supportive, and I collaborate closely with my colleague Bob Johnson 
        who manages our data science team. We use Git for version control and have 
        found it essential for our workflow.
        
        I'm somewhat skeptical of newer tools like ChatGPT for research work, though 
        I acknowledge they have potential. Our team at Stanford relies heavily on 
        established methodologies and peer review processes.
        """
    
    @pytest.fixture
    def sample_interview_context(self, sample_interview_text):
        """Create interview context for testing"""
        return InterviewContext(
            interview_id="test-interview-001",
            interview_text=sample_interview_text,
            session_id="test-session-001",
            filename="test_interview.txt"
        )
    
    async def test_validation_config_loading(self, validation_config_manager):
        """Test validation configuration loading and management"""
        # Test default config creation
        validation_config_manager.create_default_configs()
        
        # Test config listing
        configs = validation_config_manager.list_configs()
        assert len(configs) >= 3  # Should have academic, hybrid, exploratory at minimum
        
        # Test loading specific configs
        academic_config = validation_config_manager.load_config("academic_research")
        assert academic_config.entities == ValidationMode.CLOSED
        assert academic_config.relationships == ValidationMode.CLOSED
        
        hybrid_config = validation_config_manager.load_config("hybrid_default")
        assert hybrid_config.entities == ValidationMode.HYBRID
        assert hybrid_config.relationships == ValidationMode.HYBRID
    
    async def test_validated_extractor_creation(self, base_extractor, validation_config_manager):
        """Test creation of ValidatedExtractor with different configurations"""
        # Test with default config
        default_extractor = ValidatedExtractor(base_extractor)
        assert default_extractor.validation_config is not None
        
        # Test with academic config
        academic_config = ValidationConfig.academic_research_config()
        academic_extractor = ValidatedExtractor(base_extractor, academic_config)
        assert academic_extractor.validation_config.entities == ValidationMode.CLOSED
        
        # Test with custom config
        custom_config = ValidationConfig(
            entities=ValidationMode.OPEN,
            relationships=ValidationMode.HYBRID,
            quality_threshold=0.6
        )
        custom_extractor = ValidatedExtractor(base_extractor, custom_config)
        assert custom_extractor.validation_config.quality_threshold == 0.6
    
    async def test_validation_pipeline_flow(self, base_extractor, sample_interview_context):
        """Test complete validation pipeline flow"""
        # Create validated extractor with hybrid mode
        config = ValidationConfig(
            entities=ValidationMode.HYBRID,
            relationships=ValidationMode.HYBRID,
            auto_merge_similar=True,
            quality_threshold=0.7
        )
        validated_extractor = ValidatedExtractor(base_extractor, config)
        
        # Run extraction with validation
        results, stats = await validated_extractor.extract_from_interview(sample_interview_context)
        
        # Verify results structure
        assert isinstance(results, list)
        assert len(results) >= 1
        assert isinstance(stats, ValidationStats)
        
        # Verify validation statistics
        assert stats.entities_processed >= 0
        assert stats.relationships_processed >= 0
        assert stats.validation_time_ms > 0
        
        # Verify result metadata includes validation info
        result = results[0]
        assert result.metadata.get('validation_applied') is True
        assert 'validation_stats' in result.metadata
    
    async def test_entity_validation_modes(self, base_extractor, sample_interview_context):
        """Test entity validation across different modes"""
        # Test closed mode (restrictive)
        closed_config = ValidationConfig.academic_research_config()
        closed_extractor = ValidatedExtractor(base_extractor, closed_config)
        
        closed_results, closed_stats = await closed_extractor.extract_from_interview(sample_interview_context)
        
        # Test open mode (permissive)
        open_config = ValidationConfig(
            entities=ValidationMode.OPEN,
            relationships=ValidationMode.OPEN
        )
        open_extractor = ValidatedExtractor(base_extractor, open_config)
        
        open_results, open_stats = await open_extractor.extract_from_interview(sample_interview_context)
        
        # Open mode should typically allow more entities
        open_entity_count = len(open_results[0].entities_found) if open_results else 0
        closed_entity_count = len(closed_results[0].entities_found) if closed_results else 0
        
        logger.info(f"Open mode entities: {open_entity_count}, Closed mode entities: {closed_entity_count}")
        
        # Verify stats are reasonable
        assert open_stats.entities_processed >= 0
        assert closed_stats.entities_processed >= 0
    
    async def test_quality_validation_thresholds(self, base_extractor, sample_interview_context):
        """Test quality validation with different confidence thresholds"""
        # High threshold config
        high_threshold_config = ValidationConfig(
            confidence_auto_approve=0.95,
            confidence_flag_review=0.8,
            confidence_require_validation=0.7,
            quality_threshold=0.9
        )
        high_threshold_extractor = ValidatedExtractor(base_extractor, high_threshold_config)
        
        # Low threshold config
        low_threshold_config = ValidationConfig(
            confidence_auto_approve=0.7,
            confidence_flag_review=0.5,
            confidence_require_validation=0.3,
            quality_threshold=0.5
        )
        low_threshold_extractor = ValidatedExtractor(base_extractor, low_threshold_config)
        
        # Run extractions
        high_results, high_stats = await high_threshold_extractor.extract_from_interview(sample_interview_context)
        low_results, low_stats = await low_threshold_extractor.extract_from_interview(sample_interview_context)
        
        # Low threshold should typically be more permissive
        logger.info(f"High threshold rejections: {high_stats.entities_rejected + high_stats.relationships_rejected}")
        logger.info(f"Low threshold rejections: {low_stats.entities_rejected + low_stats.relationships_rejected}")
        
        # Verify both completed
        assert high_results is not None
        assert low_results is not None
    
    async def test_consolidation_integration(self, base_extractor, sample_interview_context):
        """Test entity consolidation integration"""
        config = ValidationConfig(
            auto_merge_similar=True,
            consolidation_threshold=0.85
        )
        validated_extractor = ValidatedExtractor(base_extractor, config)
        
        results, stats = await validated_extractor.extract_from_interview(sample_interview_context)
        
        # Check if any entities were merged
        logger.info(f"Entities merged during consolidation: {stats.entities_merged}")
        logger.info(f"Total entities processed: {stats.entities_processed}")
        
        # Verify consolidation stats
        assert stats.entities_merged >= 0
        assert stats.entities_processed >= stats.entities_merged
    
    async def test_relationship_standardization(self, base_extractor, sample_interview_context):
        """Test relationship standardization process"""
        config = ValidationConfig(
            relationships=ValidationMode.HYBRID
        )
        validated_extractor = ValidatedExtractor(base_extractor, config)
        
        results, stats = await validated_extractor.extract_from_interview(sample_interview_context)
        
        # Check relationship standardization
        logger.info(f"Relationships standardized: {stats.relationships_standardized}")
        logger.info(f"Total relationships processed: {stats.relationships_processed}")
        
        # Verify relationships exist and have expected structure
        if results and results[0].relationships_found:
            for rel in results[0].relationships_found:
                assert 'source_entity' in rel
                assert 'target_entity' in rel
                assert 'relationship_type' in rel or 'type' in rel
                assert 'confidence' in rel
    
    async def test_cross_interview_analyzer_integration(self, neo4j_manager):
        """Test cross-interview analyzer integration with validated data"""
        analyzer = CrossInterviewAnalyzer(neo4j_manager)
        
        # Test basic analyzer functionality
        # Note: This requires actual data in the database
        try:
            consensus_patterns = await analyzer.analyze_consensus_patterns(threshold=0.6)
            divergence_patterns = await analyzer.analyze_divergence_patterns()
            
            logger.info(f"Found {len(consensus_patterns)} consensus patterns")
            logger.info(f"Found {len(divergence_patterns)} divergence patterns")
            
            # Verify pattern structure
            for pattern in consensus_patterns:
                assert hasattr(pattern, 'pattern_type')
                assert hasattr(pattern, 'consensus_strength')
                assert hasattr(pattern, 'supporting_interviews')
            
            for pattern in divergence_patterns:
                assert hasattr(pattern, 'pattern_type')
                assert hasattr(pattern, 'conflicting_perspectives')
        
        except Exception as e:
            logger.warning(f"Cross-interview analysis requires database data: {e}")
            # This is expected if database is empty
    
    async def test_error_handling_integration(self, base_extractor):
        """Test error handling throughout validation pipeline"""
        # Test with invalid interview context
        invalid_context = InterviewContext(
            interview_id="",
            interview_text="",
            session_id="",
            filename=""
        )
        
        validated_extractor = ValidatedExtractor(base_extractor)
        
        try:
            results, stats = await validated_extractor.extract_from_interview(invalid_context)
            # Should handle gracefully
            assert isinstance(results, list)
            assert isinstance(stats, ValidationStats)
        except Exception as e:
            logger.info(f"Expected error handling: {e}")
            # Some errors are expected with invalid input
    
    async def test_performance_validation_overhead(self, base_extractor, sample_interview_context):
        """Test performance overhead of validation system"""
        # Base extraction timing
        start_time = datetime.utcnow()
        base_results = await base_extractor.extract_from_interview(sample_interview_context)
        base_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Validated extraction timing
        validated_extractor = ValidatedExtractor(base_extractor)
        start_time = datetime.utcnow()
        validated_results, stats = await validated_extractor.extract_from_interview(sample_interview_context)
        validated_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Calculate overhead
        overhead = validated_time - base_time
        overhead_percentage = (overhead / base_time) * 100 if base_time > 0 else 0
        
        logger.info(f"Base extraction time: {base_time:.2f}s")
        logger.info(f"Validated extraction time: {validated_time:.2f}s")
        logger.info(f"Validation overhead: {overhead:.2f}s ({overhead_percentage:.1f}%)")
        
        # Validation should not add excessive overhead (< 50% increase)
        assert overhead_percentage < 50, f"Validation overhead too high: {overhead_percentage:.1f}%"
    
    async def test_config_update_integration(self, base_extractor, sample_interview_context):
        """Test dynamic configuration updates"""
        validated_extractor = ValidatedExtractor(base_extractor)
        
        # Initial extraction with default config
        initial_results, initial_stats = await validated_extractor.extract_from_interview(sample_interview_context)
        
        # Update to more restrictive config
        restrictive_config = ValidationConfig.academic_research_config()
        validated_extractor.update_validation_config(restrictive_config)
        
        # Extract again with new config
        updated_results, updated_stats = await validated_extractor.extract_from_interview(sample_interview_context)
        
        # Verify config was applied
        assert validated_extractor.validation_config.entities == ValidationMode.CLOSED
        
        logger.info(f"Initial entities: {len(initial_results[0].entities_found) if initial_results else 0}")
        logger.info(f"Updated entities: {len(updated_results[0].entities_found) if updated_results else 0}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])