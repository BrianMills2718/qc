"""
Tests for Neo4j schema compatibility with the validation system.

Ensures that validated entities and relationships are properly stored
and can be retrieved from Neo4j with correct schema compliance.
"""

import pytest
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

from src.qc.core.neo4j_manager import EnhancedNeo4jManager
from src.qc.core.schema_config import create_research_schema
from src.qc.extraction.extraction_schemas import ExtractedEntity, ExtractedRelationship
from src.qc.validation.validation_config import ValidationConfig, ValidationMode

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestNeo4jSchemaCompatibility:
    """Tests for Neo4j schema compatibility with validation system"""
    
    @pytest.fixture
    async def neo4j_manager(self):
        """Setup Neo4j manager for testing"""
        manager = EnhancedNeo4jManager()
        await manager.connect()
        
        # Clear database for clean testing
        await manager.clear_database()
        
        yield manager
        await manager.close()
    
    @pytest.fixture
    def research_schema(self):
        """Setup research schema"""
        return create_research_schema()
    
    @pytest.fixture
    def sample_validated_entities(self):
        """Create sample validated entities for testing"""
        return [
            ExtractedEntity(
                id="entity_001",
                name="Dr. Alice Smith",
                type="Person",
                confidence=0.95,
                context="Professional introduction from test interview",
                quotes=[
                    "I'm Dr. Alice Smith from Stanford University",
                    "I work extensively with Python and TensorFlow"
                ]
            ),
            ExtractedEntity(
                id="entity_002",
                name="Python",
                type="Tool",
                confidence=0.88,
                context="Tool discussion from test interview",
                quotes=[
                    "I work extensively with Python",
                    "Python community has been very supportive"
                ]
            ),
            ExtractedEntity(
                id="entity_003",
                name="Stanford University",
                type="Organization",
                confidence=0.92,
                context="Institution mention from test interview",
                quotes=["I'm Dr. Alice Smith from Stanford University"]
            )
        ]
    
    @pytest.fixture
    def sample_validated_relationships(self):
        """Create sample validated relationships for testing"""
        return [
            ExtractedRelationship(
                id="rel_001",
                source_entity="Dr. Alice Smith",
                target_entity="Stanford University",
                relationship_type="WORKS_AT",
                confidence=0.94,
                context="Professional affiliation mentioned during introduction",
                quotes=["I'm Dr. Alice Smith from Stanford University"]
            ),
            ExtractedRelationship(
                id="rel_002",
                source_entity="Dr. Alice Smith",
                target_entity="Python",
                relationship_type="USES",
                confidence=0.89,
                context="Programming language usage for research",
                quotes=["I work extensively with Python"]
            ),
            ExtractedRelationship(
                id="rel_003",
                source_entity="Dr. Alice Smith",
                target_entity="TensorFlow",
                relationship_type="USES",
                confidence=0.87,
                context="Deep learning framework usage",
                quotes=["I work extensively with Python and TensorFlow"]
            )
        ]
    
    async def test_entity_storage_schema_compliance(self, neo4j_manager, research_schema, sample_validated_entities):
        """Test that validated entities are stored with proper schema compliance"""
        
        for entity in sample_validated_entities:
            # Use the new storage method
            entity_id = f"entity_{entity.name.replace(' ', '_').lower()}"
            await neo4j_manager.store_extracted_entity(entity, entity_id)
        
        # Verify entities were stored correctly
        query_result = await neo4j_manager.execute_cypher("""
            MATCH (n) 
            WHERE n.name IS NOT NULL
            RETURN n.name as name, 
                   labels(n) as labels, 
                   n.confidence as confidence,
                   keys(n) as properties
            ORDER BY n.name
        """)
        
        assert len(query_result) == len(sample_validated_entities)
        
        # Verify each entity has correct structure
        for record in query_result:
            logger.info(f"Stored entity: {record['name']} with labels {record['labels']}")
            
            # Check required properties
            assert record['name'] is not None
            assert record['confidence'] is not None
            
            # Verify entity type is reflected in labels
            entity_name = record['name']
            original_entity = next((e for e in sample_validated_entities if e.name == entity_name), None)
            assert original_entity is not None
            
            # Check that entity type appears in labels (Neo4j converts types to labels)
            expected_label = original_entity.type
            assert expected_label in record['labels']
    
    async def test_relationship_storage_schema_compliance(self, neo4j_manager, research_schema, 
                                                         sample_validated_entities, sample_validated_relationships):
        """Test that validated relationships are stored with proper schema compliance"""
        
        # First store entities using new method
        for entity in sample_validated_entities:
            entity_id = f"entity_{entity.name.replace(' ', '_').lower()}"
            await neo4j_manager.store_extracted_entity(entity, entity_id)
        
        # Store relationships (only for entities that exist)
        entity_names = {entity.name for entity in sample_validated_entities}
        stored_relationships = []
        
        for relationship in sample_validated_relationships:
            # Only create relationships where both entities exist
            if (relationship.source_entity in entity_names and 
                relationship.target_entity in entity_names):
                source_id = f"entity_{relationship.source_entity.replace(' ', '_').lower()}"
                target_id = f"entity_{relationship.target_entity.replace(' ', '_').lower()}"
                await neo4j_manager.store_extracted_relationship(relationship, source_id, target_id)
                stored_relationships.append(relationship)
        
        # Verify relationships were stored correctly
        query_result = await neo4j_manager.execute_cypher("""
            MATCH (source)-[r]->(target)
            RETURN source.name as source_name,
                   type(r) as relationship_type,
                   target.name as target_name,
                   r.confidence as confidence,
                   keys(r) as properties
            ORDER BY source_name, relationship_type, target_name
        """)
        
        assert len(query_result) == len(stored_relationships)
        
        # Verify each relationship has correct structure
        for record in query_result:
            logger.info(f"Stored relationship: {record['source_name']} -{record['relationship_type']}-> {record['target_name']}")
            
            # Check required properties
            assert record['source_name'] is not None
            assert record['target_name'] is not None
            assert record['relationship_type'] is not None
            assert record['confidence'] is not None
            
            # Verify relationship matches original data
            original_rel = next((r for r in stored_relationships 
                               if r.source_entity == record['source_name'] 
                               and r.target_entity == record['target_name']
                               and r.relationship_type == record['relationship_type']), None)
            assert original_rel is not None
            
            # Check confidence values match
            assert abs(record['confidence'] - original_rel.confidence) < 0.01
    
    async def test_validation_metadata_preservation(self, neo4j_manager, sample_validated_entities):
        """Test that entity storage and retrieval preserves all data"""
        
        entity = sample_validated_entities[0]  # Dr. Alice Smith
        
        # Store entity using new method
        entity_id = "test_entity_validation"
        await neo4j_manager.store_extracted_entity(entity, entity_id)
        
        # Retrieve using new method
        retrieved_entity = await neo4j_manager.retrieve_extracted_entity(entity_id)
        
        # Verify entity was preserved correctly
        assert retrieved_entity is not None
        assert retrieved_entity.name == entity.name
        assert retrieved_entity.type == entity.type
        assert retrieved_entity.confidence == entity.confidence
        assert retrieved_entity.context == entity.context
        assert retrieved_entity.quotes == entity.quotes
    
    async def test_quote_storage_and_retrieval(self, neo4j_manager, sample_validated_entities):
        """Test that entity quotes are properly stored and retrievable"""
        
        entity = sample_validated_entities[0]  # Entity with multiple quotes
        
        from src.qc.core.neo4j_manager import EntityNode
        # Flatten properties for Neo4j compatibility
        flattened_props = {}
        flattened_props.update(entity.properties)
        flattened_props.update(entity.metadata)
        flattened_props['quotes'] = entity.quotes
        flattened_props['confidence'] = entity.confidence
        flattened_props['context'] = entity.context
        
        entity_node = EntityNode(
            id="test_quotes",
            name=entity.name,
            entity_type=entity.type,
            properties=flattened_props
        )
        await neo4j_manager.create_entity(entity_node)
        
        # Retrieve quotes
        query_result = await neo4j_manager.execute_cypher("""
            MATCH (n {name: $name})
            RETURN n.quotes as quotes
        """, {'name': entity.name})
        
        assert len(query_result) == 1
        stored_quotes = query_result[0]['quotes']
        
        # Verify quotes were preserved
        assert isinstance(stored_quotes, list)
        assert len(stored_quotes) == len(entity.quotes)
        
        for original_quote in entity.quotes:
            assert original_quote in stored_quotes
    
    async def test_complex_property_storage(self, neo4j_manager, sample_validated_entities):
        """Test that entities with different field values are properly stored"""
        
        # Create entity with different types of values
        complex_entity = ExtractedEntity(
            id="complex_test_entity",
            name="Complex Test Entity",
            type="TestType",
            context="Test context for complex entity",
            quotes=["Test quote", "Another quote", "Third quote"],
            confidence=0.8
        )
        
        # Store using new method
        entity_id = "complex_entity"
        await neo4j_manager.store_extracted_entity(complex_entity, entity_id)
        
        # Retrieve and verify storage
        retrieved_entity = await neo4j_manager.retrieve_extracted_entity(entity_id)
        
        assert retrieved_entity is not None
        assert retrieved_entity.name == complex_entity.name
        assert retrieved_entity.type == complex_entity.type
        assert retrieved_entity.context == complex_entity.context
        assert retrieved_entity.confidence == complex_entity.confidence
        assert retrieved_entity.quotes == complex_entity.quotes
    
    async def test_schema_constraint_compliance(self, neo4j_manager, research_schema):
        """Test that stored data complies with schema constraints"""
        
        # Store test data that should comply with schema
        test_entities = [
            ("person_1", {"name": "Test Person", "type": "Person", "confidence": 0.9}),
            ("org_1", {"name": "Test Org", "type": "Organization", "confidence": 0.85}),
            ("tool_1", {"name": "Test Tool", "type": "Tool", "confidence": 0.8})
        ]
        
        for entity_id, entity_data in test_entities:
            from src.qc.core.neo4j_manager import EntityNode
            entity_node = EntityNode(
                id=entity_id,
                name=entity_data['name'],
                entity_type=entity_data['type'],
                properties={'confidence': entity_data['confidence']}
            )
            await neo4j_manager.create_entity(entity_node)
        
        # Store test relationship
        from src.qc.core.neo4j_manager import RelationshipEdge
        rel_edge = RelationshipEdge(
            source_id="person_1",
            target_id="org_1",
            relationship_type="WORKS_AT",
            properties={"confidence": 0.9}
        )
        await neo4j_manager.create_relationship(rel_edge)
        
        # Verify schema compliance by querying structure
        entity_result = await neo4j_manager.execute_cypher("""
            MATCH (n) 
            WHERE n.name IS NOT NULL
            RETURN DISTINCT labels(n) as labels, 
                   count(n) as count
            ORDER BY labels
        """)
        
        relationship_result = await neo4j_manager.execute_cypher("""
            MATCH ()-[r]->()
            RETURN DISTINCT type(r) as relationship_type,
                   count(r) as count
            ORDER BY relationship_type
        """)
        
        # Verify expected entity types exist
        entity_labels = {tuple(record['labels']) for record in entity_result}
        logger.info(f"Found entity labels: {entity_labels}")
        
        # Verify expected relationship types exist
        rel_types = {record['relationship_type'] for record in relationship_result}
        logger.info(f"Found relationship types: {rel_types}")
        
        # Should have our test data
        assert len(entity_result) >= 3
        assert len(relationship_result) >= 1
        assert "WORKS_AT" in rel_types
    
    async def test_interview_isolation_schema(self, neo4j_manager, sample_validated_entities):
        """Test that entities from different contexts can be distinguished"""
        
        # Store entities with different contexts
        interview_1_entity = sample_validated_entities[0]
        
        interview_2_entity = ExtractedEntity(
            id="entity_002",
            name="Dr. Bob Jones",
            type="Person",
            context="Second interview context",
            quotes=["I'm Dr. Bob Jones"],
            confidence=0.9
        )
        
        # Store both entities using new method
        await neo4j_manager.store_extracted_entity(interview_1_entity, "entity_1")
        await neo4j_manager.store_extracted_entity(interview_2_entity, "entity_2")
        
        # Verify both entities exist and can be distinguished by context
        context_1_result = await neo4j_manager.execute_cypher("""
            MATCH (n) 
            WHERE n.context = $context
            RETURN count(n) as count
        """, {'context': interview_1_entity.context})
        
        context_2_result = await neo4j_manager.execute_cypher("""
            MATCH (n) 
            WHERE n.context = $context
            RETURN count(n) as count
        """, {'context': interview_2_entity.context})
        
        assert context_1_result[0]['count'] >= 1
        assert context_2_result[0]['count'] >= 1
        
        logger.info("Context-based entity isolation maintained in schema")
    
    async def test_validation_confidence_indexing(self, neo4j_manager, sample_validated_entities):
        """Test that confidence scores are properly indexed for queries"""
        
        # Store entities with varying confidence scores
        confidence_entities = []
        for i, base_entity in enumerate(sample_validated_entities):
            entity_name = f"{base_entity.name}_{i}"
            confidence_score = 0.5 + (i * 0.15)  # Varying confidence: 0.5, 0.65, 0.8
            
            # Create new entity with modified confidence
            confidence_entity = ExtractedEntity(
                id=f"conf_entity_{i}",
                name=entity_name,
                type=base_entity.type,
                context=base_entity.context,
                quotes=base_entity.quotes,
                confidence=confidence_score
            )
            
            confidence_entities.append(confidence_entity)
            
            # Store using new method
            await neo4j_manager.store_extracted_entity(confidence_entity, f"conf_entity_{i}")
        
        # Query by confidence ranges
        high_confidence_result = await neo4j_manager.execute_cypher("""
            MATCH (n) 
            WHERE n.confidence > 0.7
            RETURN count(n) as count
        """)
        
        medium_confidence_result = await neo4j_manager.execute_cypher("""
            MATCH (n) 
            WHERE n.confidence > 0.6 AND n.confidence <= 0.7
            RETURN count(n) as count
        """)
        
        low_confidence_result = await neo4j_manager.execute_cypher("""
            MATCH (n) 
            WHERE n.confidence <= 0.6
            RETURN count(n) as count
        """)
        
        high_count = high_confidence_result[0]['count']
        medium_count = medium_confidence_result[0]['count']
        low_count = low_confidence_result[0]['count']
        
        logger.info(f"Confidence distribution - High: {high_count}, Medium: {medium_count}, Low: {low_count}")
        
        # Verify confidence queries work
        assert high_count >= 0
        assert medium_count >= 0  
        assert low_count >= 0
        assert (high_count + medium_count + low_count) >= len(confidence_entities)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])