"""
Enhanced Neo4j Manager for Dynamic Entity-Relationship System

This module provides a complete Neo4j integration for flexible entity types
with dynamic properties and relationships.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
import os

from neo4j import AsyncGraphDatabase
from neo4j.exceptions import Neo4jError

logger = logging.getLogger(__name__)


@dataclass
class EntityNode:
    """Represents a flexible entity node"""
    id: str
    name: str
    entity_type: str
    properties: Dict[str, Any]
    labels: List[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = ["Entity", self.entity_type]


@dataclass
class RelationshipEdge:
    """Represents a relationship between entities"""
    source_id: str
    target_id: str
    relationship_type: str
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class EnhancedNeo4jManager:
    """Enhanced Neo4j manager with dynamic entity support"""
    
    def __init__(self, uri: str = None, username: str = None, password: str = None):
        """Initialize with connection parameters"""
        # FAIL-FAST: Runtime parameter validation
        if uri is not None and not isinstance(uri, str):
            raise TypeError(f"uri must be str, got {type(uri)}")
        if username is not None and not isinstance(username, str):
            raise TypeError(f"username must be str, got {type(username)}")
        if password is not None and not isinstance(password, str):
            raise TypeError(f"password must be str, got {type(password)}")
        
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        # Handle authentication disabled case - empty env vars should result in None
        self.username = username if username is not None else (os.getenv("NEO4J_USERNAME") or None)
        self.password = password if password is not None else (os.getenv("NEO4J_PASSWORD") or None)
        self.driver = None
        
        # Debug logging
        logger.info(f"Neo4j config - URI: {self.uri}, Username: {self.username}, Password: {'***' if self.password else None}")
        
    async def connect(self):
        """Establish connection to Neo4j"""
        try:
            # Handle no authentication case
            if self.username is None or self.password is None:
                self.driver = AsyncGraphDatabase.driver(self.uri)
            else:
                self.driver = AsyncGraphDatabase.driver(
                    self.uri, 
                    auth=(self.username, self.password)
                )
            # Verify connectivity
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {self.uri}")
            
            # Create indexes
            await self._create_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
            
    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Closed Neo4j connection")
    
    async def _create_indexes(self):
        """Create indexes for enhanced schema"""
        indexes = [
            # Entity indexes
            "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)",
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            
            # Code indexes
            "CREATE INDEX code_name_idx IF NOT EXISTS FOR (c:Code) ON (c.name)",
            "CREATE CONSTRAINT code_id_unique IF NOT EXISTS FOR (c:Code) REQUIRE c.id IS UNIQUE",
            
            # Quote indexes (for quote-centric architecture)
            "CREATE INDEX quote_interview_idx IF NOT EXISTS FOR (q:Quote) ON (q.interview_id)",
            "CREATE INDEX quote_line_range_idx IF NOT EXISTS FOR (q:Quote) ON (q.line_start, q.line_end)",
            "CREATE INDEX quote_confidence_idx IF NOT EXISTS FOR (q:Quote) ON (q.confidence)",
            "CREATE CONSTRAINT quote_id_unique IF NOT EXISTS FOR (q:Quote) REQUIRE q.id IS UNIQUE",
            
            # Performance indexes
            "CREATE INDEX entity_type_name IF NOT EXISTS FOR (e:Entity) ON (e.entity_type, e.name)",
            "CREATE INDEX quote_semantic_type_idx IF NOT EXISTS FOR (q:Quote) ON (q.semantic_type)",
            
            # Dialogue structure indexes (NEW)
            "CREATE INDEX dialogue_turn_sequence_idx IF NOT EXISTS FOR (t:DialogueTurn) ON (t.sequence_number)",
            "CREATE INDEX dialogue_turn_speaker_idx IF NOT EXISTS FOR (t:DialogueTurn) ON (t.speaker_name)",
            "CREATE CONSTRAINT dialogue_turn_id_unique IF NOT EXISTS FOR (t:DialogueTurn) REQUIRE t.turn_id IS UNIQUE",
            
            # Thematic connection indexes (NEW)
            "CREATE INDEX thematic_connection_type_idx IF NOT EXISTS FOR (c:ThematicConnection) ON (c.connection_type)",
            "CREATE INDEX thematic_connection_confidence_idx IF NOT EXISTS FOR (c:ThematicConnection) ON (c.confidence_score)",
            
            # Quote sequence position index (NEW) 
            "CREATE INDEX quote_sequence_position_idx IF NOT EXISTS FOR (q:Quote) ON (q.sequence_position)",
        ]
        
        async with self.driver.session() as session:
            for index in indexes:
                try:
                    await session.run(index)
                except Neo4jError as e:
                    # Constraint might already exist
                    if "already exists" not in str(e):
                        logger.warning(f"Index creation warning: {e}")
    
    async def ensure_connected(self):
        """Ensure Neo4j connection is alive"""
        try:
            async with self.driver.session() as session:
                await session.run("RETURN 1")
        except Exception:
            # Reconnect
            logger.info("Reconnecting to Neo4j...")
            await self.connect()
    
    async def create_entity(self, entity: EntityNode) -> str:
        """
        Create a flexible entity node with dynamic properties
        
        Args:
            entity: EntityNode with id, name, type, and properties
            
        Returns:
            The entity ID
        """
        await self.ensure_connected()
        
        # Build labels string
        labels_str = ":".join(entity.labels)
        
        # Prepare properties - combine base properties with custom ones
        all_properties = {
            "id": entity.id,
            "name": entity.name,
            "entity_type": entity.entity_type,
            "created_at": datetime.utcnow().isoformat(),
            **entity.properties
        }
        
        query = f"""
        CREATE (e:{labels_str})
        SET e = $properties
        RETURN e.id as id
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, properties=all_properties)
            record = await result.single()
            
            logger.info(f"Created entity: {entity.entity_type} - {entity.name}")
            return record["id"]
    
    async def create_relationship(self, edge: RelationshipEdge) -> bool:
        """
        Create a relationship between entities
        
        Args:
            edge: RelationshipEdge with source, target, type, and properties
            
        Returns:
            True if successful
        """
        await self.ensure_connected()
        
        # Add metadata to relationship
        rel_properties = {
            "created_at": datetime.utcnow().isoformat(),
            **edge.properties
        }
        
        query = f"""
        MATCH (source:Entity {{id: $source_id}})
        MATCH (target:Entity {{id: $target_id}})
        CREATE (source)-[r:{edge.relationship_type}]->(target)
        SET r = $properties
        RETURN r
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                source_id=edge.source_id,
                target_id=edge.target_id,
                properties=rel_properties
            )
            
            if await result.single():
                logger.info(f"Created relationship: {edge.source_id} -{edge.relationship_type}-> {edge.target_id}")
                return True
            return False
    
    async def create_code(self, code_data: Dict[str, Any]) -> str:
        """
        Create a thematic code node
        
        Args:
            code_data: Dictionary with code information
            
        Returns:
            The code ID
        """
        await self.ensure_connected()
        
        code_id = code_data.get('id', f"code_{datetime.utcnow().timestamp()}")
        
        query = """
        CREATE (c:Code {
            id: $id,
            name: $name,
            definition: $definition,
            created_at: $created_at,
            parent_id: $parent_id,
            level: $level,
            child_codes: $child_codes
        })
        RETURN c.id as id
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                id=code_id,
                name=code_data['name'],
                definition=code_data.get('definition', ''),
                created_at=datetime.utcnow().isoformat(),
                parent_id=code_data.get('parent_id'),
                level=code_data.get('level', 0),
                child_codes=json.dumps(code_data.get('child_codes', []))
            )
            record = await result.single()
            
            logger.info(f"Created code: {code_data['name']}")
            return record["id"]
    
    async def link_entity_to_code(self, entity_id: str, code_id: str, 
                                  context: str, confidence: float = 1.0) -> bool:
        """
        Create a MENTIONS relationship between an entity and a code
        
        Args:
            entity_id: Entity ID
            code_id: Code ID
            context: Quote or context for the relationship
            confidence: Confidence score (0-1)
            
        Returns:
            True if successful
        """
        await self.ensure_connected()
        
        query = """
        MATCH (e:Entity {id: $entity_id})
        MATCH (c:Code {id: $code_id})
        CREATE (e)-[r:MENTIONS {
            context: $context,
            confidence: $confidence,
            created_at: $created_at
        }]->(c)
        RETURN r
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                entity_id=entity_id,
                code_id=code_id,
                context=context,
                confidence=confidence,
                created_at=datetime.utcnow().isoformat()
            )
            
            if await result.single():
                logger.info(f"Linked entity {entity_id} to code {code_id}")
                return True
            return False
    
    async def execute_cypher(self, cypher: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results
        
        Args:
            cypher: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        await self.ensure_connected()
        
        async with self.driver.session() as session:
            result = await session.run(cypher, parameters or {})
            records = []
            async for record in result:
                records.append(dict(record))
            return records
    
    async def bulk_create_entities(self, entities: List[EntityNode]) -> int:
        """
        Create multiple entities in a single transaction
        
        Args:
            entities: List of EntityNode objects
            
        Returns:
            Number of entities created
        """
        await self.ensure_connected()
        
        query = """
        UNWIND $entities as entity
        CREATE (e:Entity)
        SET e = entity.properties
        SET e.id = entity.id
        SET e.name = entity.name
        SET e.entity_type = entity.entity_type
        SET e.created_at = $created_at
        RETURN count(e) as count
        """
        
        entities_data = []
        for entity in entities:
            labels = ":".join(entity.labels)
            entities_data.append({
                "id": entity.id,
                "name": entity.name,
                "entity_type": entity.entity_type,
                "properties": entity.properties,
                "labels": labels
            })
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                entities=entities_data,
                created_at=datetime.utcnow().isoformat()
            )
            record = await result.single()
            count = record["count"]
            
            logger.info(f"Bulk created {count} entities")
            return count
    
    async def get_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID"""
        await self.ensure_connected()
        
        query = """
        MATCH (e:Entity {id: $entity_id})
        RETURN e
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, entity_id=entity_id)
            record = await result.single()
            
            if record:
                return dict(record["e"])
            return None
    
    async def find_entities_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Find all entities of a specific type"""
        await self.ensure_connected()
        
        query = """
        MATCH (e:Entity {entity_type: $entity_type})
        RETURN e
        ORDER BY e.name
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, entity_type=entity_type)
            entities = []
            async for record in result:
                entities.append(dict(record["e"]))
            return entities
    
    async def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        await self.ensure_connected()
        
        query = "MATCH (n) DETACH DELETE n"
        
        async with self.driver.session() as session:
            await session.run(query)
            logger.warning("Cleared all nodes and relationships from database")
    
    async def store_extracted_entity(self, entity, entity_id: str = None) -> str:
        """
        Store an ExtractedEntity using Neo4j-compatible format
        
        Args:
            entity: ExtractedEntity object  
            entity_id: Optional custom entity ID
            
        Returns:
            The entity ID
        """
        from qc.extraction.extraction_schemas import ExtractedEntity
        
        # Ensure we have an ExtractedEntity
        if not isinstance(entity, ExtractedEntity):
            raise TypeError(f"Expected ExtractedEntity, got {type(entity)}")
        
        # Use provided ID or generate one
        if entity_id is None:
            entity_id = entity.id if entity.id else f"entity_{entity.name.replace(' ', '_').lower()}"
        
        # Convert to Neo4j-compatible format (excludes name, type, id which are handled separately)
        neo4j_data = entity.to_neo4j_dict()
        # Remove the core fields that are handled by EntityNode itself
        properties_only = {k: v for k, v in neo4j_data.items() if k not in ['name', 'type', 'id']}
        
        # Create EntityNode for storage
        entity_node = EntityNode(
            id=entity_id,
            name=entity.name,
            entity_type=entity.type,
            properties=properties_only
        )
        
        stored_id = await self.create_entity(entity_node)
        return stored_id if stored_id else entity_id
    
    async def retrieve_extracted_entity(self, entity_id: str):
        """
        Retrieve an entity and convert back to ExtractedEntity
        
        Args:
            entity_id: Entity ID to retrieve
            
        Returns:
            ExtractedEntity object or None if not found
        """
        from qc.extraction.extraction_schemas import ExtractedEntity
        
        neo4j_data = await self.get_entity_by_id(entity_id)
        if neo4j_data:
            return ExtractedEntity.from_neo4j_dict(neo4j_data)
        return None
    
    async def store_extracted_relationship(self, relationship, source_id: str, target_id: str) -> bool:
        """
        Store an ExtractedRelationship using Neo4j-compatible format
        
        Args:
            relationship: ExtractedRelationship object
            source_id: Source entity ID in Neo4j
            target_id: Target entity ID in Neo4j
            
        Returns:
            True if successful
        """
        from qc.extraction.extraction_schemas import ExtractedRelationship
        
        # Ensure we have an ExtractedRelationship
        if not isinstance(relationship, ExtractedRelationship):
            raise TypeError(f"Expected ExtractedRelationship, got {type(relationship)}")
        
        # Convert to Neo4j-compatible format
        neo4j_data = relationship.to_neo4j_dict()
        
        # Create RelationshipEdge for storage
        rel_edge = RelationshipEdge(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship.relationship_type,
            properties=neo4j_data
        )
        
        return await self.create_relationship(rel_edge)
    
    # Quote-Centric Architecture Methods
    
    async def create_quote_node(self, quote_data: Dict[str, Any]) -> str:
        """
        Create a Quote node with semantic properties
        
        Args:
            quote_data: Dictionary with quote information including:
                - text: Quote text content
                - line_start: Starting line number
                - line_end: Ending line number 
                - interview_id: Source interview identifier
                - speaker: Optional speaker identifier
                - context: Optional surrounding context
                - confidence: Optional confidence score (0.0-1.0)
                - semantic_type: Optional semantic unit type (sentence/paragraph/line)
                
        Returns:
            The quote ID
        """
        await self.ensure_connected()
        
        # Generate quote ID if not provided
        quote_id = quote_data.get('id', f"quote_{datetime.utcnow().timestamp()}")
        
        # Prepare quote properties with defaults
        quote_properties = {
            "id": quote_id,
            "text": quote_data['text'],
            "line_start": quote_data['line_start'],
            "line_end": quote_data['line_end'],
            "line_number": quote_data['line_start'],  # Backward compatibility
            "interview_id": quote_data['interview_id'],
            "speaker": quote_data.get('speaker', ''),
            "context": quote_data.get('context', ''),
            "confidence": quote_data.get('confidence', 0.0),
            "semantic_type": quote_data.get('semantic_type', 'paragraph'),
            "created_at": datetime.utcnow().isoformat()
        }
        
        query = """
        CREATE (q:Quote)
        SET q = $properties
        RETURN q.id as id
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, properties=quote_properties)
            record = await result.single()
            
            logger.info(f"Created quote: {quote_id} from {quote_data['interview_id']} lines {quote_data['line_start']}-{quote_data['line_end']}")
            return record["id"]
    
    async def link_quote_to_entity(self, quote_id: str, entity_id: str, 
                                  relationship_type: str = "MENTIONS") -> bool:
        """
        Create a relationship between a Quote and an Entity
        
        Args:
            quote_id: Quote node ID
            entity_id: Entity node ID
            relationship_type: Type of relationship (default: MENTIONS)
            
        Returns:
            True if successful
        """
        await self.ensure_connected()
        
        query = f"""
        MATCH (q:Quote {{id: $quote_id}})
        MATCH (e:Entity {{id: $entity_id}})
        CREATE (q)-[r:{relationship_type} {{
            created_at: $created_at,
            confidence: q.confidence
        }}]->(e)
        RETURN r
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                quote_id=quote_id,
                entity_id=entity_id,
                created_at=datetime.utcnow().isoformat()
            )
            
            if await result.single():
                logger.info(f"Linked quote {quote_id} to entity {entity_id} via {relationship_type}")
                return True
            return False
    
    async def link_quote_to_code(self, quote_id: str, code_id: str, 
                                relationship_type: str = "SUPPORTS") -> bool:
        """
        Create a relationship between a Quote and a Code
        
        Args:
            quote_id: Quote node ID
            code_id: Code node ID
            relationship_type: Type of relationship (default: SUPPORTS)
            
        Returns:
            True if successful
        """
        await self.ensure_connected()
        
        query = f"""
        MATCH (q:Quote {{id: $quote_id}})
        MATCH (c:Code {{id: $code_id}})
        CREATE (q)-[r:{relationship_type} {{
            created_at: $created_at,
            confidence: q.confidence
        }}]->(c)
        RETURN r
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                quote_id=quote_id,
                code_id=code_id,
                created_at=datetime.utcnow().isoformat()
            )
            
            if await result.single():
                logger.info(f"Linked quote {quote_id} to code {code_id} via {relationship_type}")
                return True
            return False
    
    async def find_quotes_by_line_range(self, interview_id: str, start_line: int, end_line: int) -> List[Dict]:
        """
        Find quotes within a specific line range in an interview
        
        Args:
            interview_id: Interview identifier
            start_line: Starting line number
            end_line: Ending line number
            
        Returns:
            List of quote dictionaries
        """
        await self.ensure_connected()
        
        query = """
        MATCH (q:Quote)
        WHERE q.interview_id = $interview_id 
        AND q.line_start >= $start_line 
        AND q.line_end <= $end_line
        RETURN q
        ORDER BY q.line_start
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                interview_id=interview_id,
                start_line=start_line,
                end_line=end_line
            )
            quotes = []
            async for record in result:
                quotes.append(dict(record["q"]))
            return quotes
    
    async def create_quote_indexes(self):
        """Create optimized indexes for quote operations"""
        await self.ensure_connected()
        
        # Additional strategic indexes for quote performance
        additional_indexes = [
            "CREATE INDEX quote_text_fulltext IF NOT EXISTS FOR (q:Quote) ON (q.text)",
            "CREATE INDEX quote_interview_line IF NOT EXISTS FOR (q:Quote) ON (q.interview_id, q.line_start)",
            "CREATE INDEX quote_confidence_interview IF NOT EXISTS FOR (q:Quote) ON (q.confidence, q.interview_id)",
        ]
        
        async with self.driver.session() as session:
            for index in additional_indexes:
                try:
                    await session.run(index)
                    logger.info(f"Created quote index: {index}")
                except Neo4jError as e:
                    if "already exists" not in str(e):
                        logger.warning(f"Quote index creation warning: {e}")
    
    async def optimize_quote_storage(self, relevance_threshold: float = 0.5):
        """
        Optimize quote storage by implementing relevance filtering
        
        Args:
            relevance_threshold: Minimum confidence score to keep quotes
        """
        await self.ensure_connected()
        
        # Archive low-relevance quotes instead of deleting
        query = """
        MATCH (q:Quote)
        WHERE q.confidence < $threshold
        SET q.archived = true, q.archived_at = $archived_at
        RETURN count(q) as archived_count
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                threshold=relevance_threshold,
                archived_at=datetime.utcnow().isoformat()
            )
            record = await result.single()
            archived_count = record["archived_count"]
            
            if archived_count > 0:
                logger.info(f"Archived {archived_count} low-relevance quotes (confidence < {relevance_threshold})")
            
            return archived_count
    
    async def get_quote_by_id(self, quote_id: str) -> Optional[Dict[str, Any]]:
        """Get quote by ID"""
        await self.ensure_connected()
        
        query = """
        MATCH (q:Quote {id: $quote_id})
        RETURN q
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, quote_id=quote_id)
            record = await result.single()
            
            if record:
                return dict(record["q"])
            return None
    
    async def find_quotes_by_interview(self, interview_id: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Find all quotes from a specific interview"""
        await self.ensure_connected()
        
        where_clause = "WHERE q.interview_id = $interview_id"
        if not include_archived:
            where_clause += " AND (q.archived IS NULL OR q.archived = false)"
        
        query = f"""
        MATCH (q:Quote)
        {where_clause}
        RETURN q
        ORDER BY q.line_start
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, interview_id=interview_id)
            quotes = []
            async for record in result:
                quotes.append(dict(record["q"]))
            return quotes

    # Automation Display Methods
    
    async def get_automation_summary(self, interview_ids: List[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive automation summary statistics
        
        Args:
            interview_ids: Optional list of interview IDs to filter by
            
        Returns:
            Dictionary with automation statistics and timeline
        """
        await self.ensure_connected()
        
        # Build interview filter
        interview_filter = ""
        params = {}
        if interview_ids:
            interview_filter = "WHERE q.interview_id IN $interview_ids"
            params["interview_ids"] = interview_ids
        
        # Get overall statistics - CORRECTED aggregation logic
        stats_query = f"""
        MATCH (q:Quote)
        {interview_filter}
        WITH collect(DISTINCT q.interview_id) as interview_ids, collect(q) as all_quotes
        UNWIND all_quotes as q
        OPTIONAL MATCH (e:Entity)
        OPTIONAL MATCH (q)-[r1:MENTIONS]->(e2:Entity)
        OPTIONAL MATCH (q)-[r2:SUPPORTS]->(c:Code)
        RETURN 
            count(DISTINCT q) as quotes_extracted,
            size(interview_ids) as interviews_processed,
            count(DISTINCT e) as entities_detected,
            count(DISTINCT r1) as entity_relationships,  
            count(DISTINCT r2) as code_assignments,
            interview_ids
        """
        
        # Get confidence distribution
        conf_query = f"""
        MATCH (q:Quote)
        {interview_filter}
        WHERE q.confidence IS NOT NULL
        WITH q.confidence as conf
        RETURN 
            sum(CASE WHEN conf >= 0.8 THEN 1 ELSE 0 END) as high,
            sum(CASE WHEN conf >= 0.6 AND conf < 0.8 THEN 1 ELSE 0 END) as medium,
            sum(CASE WHEN conf < 0.6 THEN 1 ELSE 0 END) as low
        """
        
        # Get processing timeline
        timeline_query = f"""
        MATCH (q:Quote)
        {interview_filter}
        WITH q.interview_id as interview_id, q
        OPTIONAL MATCH (q)-[:MENTIONS]->(e:Entity)
        RETURN 
            interview_id,
            count(DISTINCT q) as quotes,
            count(DISTINCT e) as entities
        ORDER BY interview_id
        """
        
        async with self.driver.session() as session:
            # Get statistics
            stats_result = await session.run(stats_query, params)
            stats_record = await stats_result.single()
            
            statistics = {
                "quotes_extracted": stats_record["quotes_extracted"] or 0,
                "quote_nodes": stats_record["quotes_extracted"] or 0,  # Same as quotes_extracted
                "interviews_processed": stats_record["interviews_processed"] or 0,
                "entities_detected": stats_record["entities_detected"] or 0,
                "entity_relationships": stats_record["entity_relationships"] or 0,
                "code_assignments": stats_record["code_assignments"] or 0
            }
            
            # Get confidence distribution
            conf_result = await session.run(conf_query, params)
            conf_record = await conf_result.single()
            
            confidence_distribution = {
                "high": conf_record["high"] or 0,
                "medium": conf_record["medium"] or 0,
                "low": conf_record["low"] or 0
            } if conf_record else {}
            
            # Get timeline
            timeline_result = await session.run(timeline_query, params)
            timeline = {}
            async for record in timeline_result:
                timeline[record["interview_id"]] = {
                    "quotes": record["quotes"],
                    "entities": record["entities"]
                }
            
            return {
                "statistics": statistics,
                "confidence_distribution": confidence_distribution,
                "timeline": timeline,
                "interview_ids": stats_record["interview_ids"] or []
            }
    
    async def get_quotes_with_assignments(self, interview_id: str, include_confidence: bool = True) -> List[Dict]:
        """
        Get quotes with their automated entity/code assignments and confidence scores
        
        Args:
            interview_id: Interview ID to retrieve quotes for
            include_confidence: Whether to include confidence scores
            
        Returns:
            List of quotes with their assignments
        """
        await self.ensure_connected()
        
        query = """
        MATCH (q:Quote {interview_id: $interview_id})
        OPTIONAL MATCH (q)-[re:MENTIONS]->(e:Entity)
        OPTIONAL MATCH (q)-[rc:SUPPORTS]->(c:Code)
        RETURN 
            q,
            collect(DISTINCT {
                id: e.id,
                name: e.name,
                entity_type: e.entity_type,
                confidence: re.confidence
            }) as entities,
            collect(DISTINCT {
                id: c.id,
                name: c.name,
                code_type: c.code_type,
                confidence: rc.confidence
            }) as codes
        ORDER BY q.line_start
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, interview_id=interview_id)
            quotes = []
            
            async for record in result:
                quote_data = dict(record["q"])
                
                # Add entity and code relationships
                entities = [e for e in record["entities"] if e["id"] is not None]
                codes = [c for c in record["codes"] if c["id"] is not None]
                
                quote_data["entities"] = entities
                quote_data["codes"] = codes
                
                quotes.append(quote_data)
            
            return quotes
    
    async def get_automated_patterns_disabled(self, interview_ids: List[str] = None, min_confidence: float = 0.7) -> List[Dict]:
        """
        Extract automatically detected patterns and themes across interviews
        
        Args:
            interview_ids: Optional list of interview IDs to analyze
            min_confidence: Minimum confidence threshold for patterns
            
        Returns:
            List of detected patterns with supporting evidence
        """
        await self.ensure_connected()
        
        # Build interview filter
        interview_filter = ""
        params = {"min_confidence": min_confidence}
        if interview_ids:
            interview_filter = "AND q.interview_id IN $interview_ids"
            params["interview_ids"] = interview_ids
        
        # Find patterns by entity co-occurrence
        entity_patterns_query = f"""
        MATCH (q1:Quote)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(q2:Quote)
        WHERE q1.confidence >= $min_confidence 
        AND q2.confidence >= $min_confidence 
        AND q1 <> q2
        {interview_filter.replace('q.', 'q1.')}
        {interview_filter.replace('q.', 'q2.')}
        WITH e, collect(DISTINCT q1) + collect(DISTINCT q2) as quotes
        WHERE size(quotes) >= 3
        WITH e, quotes,
             [q IN quotes WHERE q.confidence IS NOT NULL | q.confidence] as confidences
        RETURN 
            'entity_pattern' as pattern_type,
            e.name as name,
            e.entity_type + ' pattern' as description,
            size(quotes) as frequency,
            CASE WHEN size(confidences) > 0 
                 THEN reduce(sum = 0.0, c IN confidences | sum + c) / size(confidences) 
                 ELSE 0.0 
            END as confidence,
            [q IN quotes[0..5] | {id: q.id, text: q.text, confidence: q.confidence}] as supporting_quotes,
            size([q IN quotes | q.interview_id]) > 1 as cross_interview
        ORDER BY frequency DESC
        LIMIT 20
        """
        
        # Find code co-occurrence patterns
        code_patterns_query = f"""
        MATCH (q1:Quote)-[:SUPPORTS]->(c:Code)<-[:SUPPORTS]-(q2:Quote)
        WHERE q1.confidence >= $min_confidence 
        AND q2.confidence >= $min_confidence 
        AND q1 <> q2
        {interview_filter.replace('q.', 'q1.')}
        {interview_filter.replace('q.', 'q2.')}
        WITH c, collect(DISTINCT q1) + collect(DISTINCT q2) as quotes
        WHERE size(quotes) >= 3
        WITH c, quotes,
             [q IN quotes WHERE q.confidence IS NOT NULL | q.confidence] as confidences
        RETURN 
            'code_pattern' as pattern_type,
            c.name as name,
            COALESCE(c.code_type, c.name) + ' theme' as description,
            size(quotes) as frequency,
            CASE WHEN size(confidences) > 0 
                 THEN reduce(sum = 0.0, conf IN confidences | sum + conf) / size(confidences) 
                 ELSE 0.0 
            END as confidence,
            [q IN quotes[0..5] | {id: q.id, text: q.text, confidence: q.confidence}] as supporting_quotes,
            size([q IN quotes | q.interview_id]) > 1 as cross_interview
        ORDER BY frequency DESC
        LIMIT 20
        """
        
        async with self.driver.session() as session:
            patterns = []
            
            # Get entity patterns
            entity_result = await session.run(entity_patterns_query, params)
            async for record in entity_result:
                pattern = dict(record)
                # Convert supporting quotes to dictionaries
                pattern["supporting_quotes"] = [dict(q) for q in pattern["supporting_quotes"]]
                patterns.append(pattern)
            
            # Get code patterns
            code_result = await session.run(code_patterns_query, params)
            async for record in code_result:
                pattern = dict(record)
                # Convert supporting quotes to dictionaries
                pattern["supporting_quotes"] = [dict(q) for q in pattern["supporting_quotes"]]
                patterns.append(pattern)
            
            # Sort by confidence and frequency
            patterns.sort(key=lambda x: (x["confidence"], x["frequency"]), reverse=True)
            
            return patterns
    
    async def get_provenance_chain(self, finding_id: str, finding_type: str) -> Dict[str, Any]:
        """
        Build complete provenance chain from findings to source quotes with line numbers
        
        Args:
            finding_id: ID of the finding (entity or code)
            finding_type: Type of finding ('entity' or 'code')
            
        Returns:
            Complete provenance chain with evidence trail
        """
        await self.ensure_connected()
        
        if finding_type.lower() == 'entity':
            query = """
            MATCH (e:Entity {id: $finding_id})
            OPTIONAL MATCH (q:Quote)-[r:MENTIONS]->(e)
            RETURN 
                e as finding,
                'entity' as finding_type,
                collect({
                    quote: q,
                    relationship: r,
                    confidence: r.confidence,
                    line_start: q.line_start,
                    line_end: q.line_end,
                    interview_id: q.interview_id,
                    text: q.text,
                    context: q.context
                }) as evidence_chain
            """
        elif finding_type.lower() == 'code':
            query = """
            MATCH (c:Code {id: $finding_id})
            OPTIONAL MATCH (q:Quote)-[r:SUPPORTS]->(c)
            RETURN 
                c as finding,
                'code' as finding_type,
                collect({
                    quote: q,
                    relationship: r,
                    confidence: r.confidence,
                    line_start: q.line_start,
                    line_end: q.line_end,
                    interview_id: q.interview_id,
                    text: q.text,
                    context: q.context
                }) as evidence_chain
            """
        else:
            raise ValueError(f"Unsupported finding type: {finding_type}")
        
        async with self.driver.session() as session:
            result = await session.run(query, finding_id=finding_id)
            record = await result.single()
            
            if not record:
                return {"error": f"Finding {finding_id} not found"}
            
            # Build provenance chain
            provenance = {
                "finding": dict(record["finding"]),
                "finding_type": record["finding_type"],
                "evidence_count": len(record["evidence_chain"]),
                "evidence_chain": []
            }
            
            # Process evidence chain
            for evidence in record["evidence_chain"]:
                if evidence["quote"]:
                    evidence_item = {
                        "quote_id": evidence["quote"]["id"],
                        "interview_id": evidence["interview_id"],
                        "line_range": f"{evidence['line_start']}-{evidence['line_end']}",
                        "text": evidence["text"],
                        "context": evidence["context"],
                        "confidence": evidence["confidence"],
                        "relationship_type": evidence["relationship"]["type"] if evidence["relationship"] else None
                    }
                    provenance["evidence_chain"].append(evidence_item)
            
            # Sort evidence by interview and line number
            provenance["evidence_chain"].sort(key=lambda x: (x["interview_id"], int(x["line_range"].split("-")[0])))
            
            return provenance