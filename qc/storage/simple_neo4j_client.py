"""
Simple Neo4j Client for Qualitative Coding Results

Minimal implementation to support local Neo4j Desktop connection and
basic graph operations for storing qualitative coding analysis.

No production features like connection pooling - designed for research use.
"""
import os
import logging
import asyncio
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import json

# Neo4j driver imports
try:
    from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
    from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError
    NEO4J_AVAILABLE = True
except ImportError:
    # For environments without neo4j driver installed
    NEO4J_AVAILABLE = False
    AsyncGraphDatabase = None
    AsyncDriver = None
    AsyncSession = None
    ServiceUnavailable = Exception
    AuthError = Exception
    ClientError = Exception

from qc.models.comprehensive_analysis_models import GlobalCodingResult, EnhancedResult

logger = logging.getLogger(__name__)


class Neo4jConnectionError(Exception):
    """Raised when Neo4j connection fails."""
    pass


class SimpleNeo4jClient:
    """
    Simple Neo4j client for local development and research.
    
    Connects to Neo4j Desktop instance running locally.
    No production features - designed for single-user research.
    """
    
    def __init__(
        self, 
        uri: str = None,
        username: str = None,
        password: str = None
    ):
        """
        Initialize Neo4j client.
        
        Args:
            uri: Neo4j connection URI (default: bolt://localhost:7687)
            username: Neo4j username (default: neo4j)
            password: Neo4j password (from env NEO4J_PASSWORD)
        """
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = username or os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'password')
        
        self.driver: Optional[AsyncDriver] = None
        self.is_connected = False
        
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available. Install with: pip install neo4j")
    
    async def connect(self) -> None:
        """Establish connection to Neo4j database."""
        if not NEO4J_AVAILABLE:
            raise Neo4jConnectionError("Neo4j driver not installed")
        
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            
            # Verify connectivity
            await self.driver.verify_connectivity()
            self.is_connected = True
            
            logger.info(f"Connected to Neo4j at {self.uri}")
            
        except (ServiceUnavailable, AuthError) as e:
            raise Neo4jConnectionError(f"Failed to connect to Neo4j: {str(e)}")
        except Exception as e:
            raise Neo4jConnectionError(f"Unexpected connection error: {str(e)}")
    
    async def connect_with_retry(self, max_retries: int = 3) -> None:
        """Connect with retry mechanism."""
        for attempt in range(max_retries):
            try:
                await self.connect()
                return
            except Neo4jConnectionError as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def close(self) -> None:
        """Close connection to Neo4j."""
        if self.driver:
            await self.driver.close()
            self.driver = None
            self.is_connected = False
            logger.info("Neo4j connection closed")
    
    async def create_schema(self) -> None:
        """Create basic schema for qualitative coding."""
        if not self.is_connected:
            raise Neo4jConnectionError("Not connected to Neo4j")
        
        # Create constraints and indexes
        schema_queries = [
            # Node constraints
            "CREATE CONSTRAINT interview_id IF NOT EXISTS FOR (i:Interview) REQUIRE i.interview_id IS UNIQUE",
            "CREATE CONSTRAINT code_id IF NOT EXISTS FOR (c:Code) REQUIRE c.code_id IS UNIQUE", 
            "CREATE CONSTRAINT theme_id IF NOT EXISTS FOR (t:Theme) REQUIRE t.theme_id IS UNIQUE",
            "CREATE CONSTRAINT category_id IF NOT EXISTS FOR (cat:Category) REQUIRE cat.category_id IS UNIQUE",
            "CREATE CONSTRAINT quote_id IF NOT EXISTS FOR (q:Quote) REQUIRE q.quote_id IS UNIQUE",
            
            # Indexes for performance
            "CREATE INDEX interview_name IF NOT EXISTS FOR (i:Interview) ON (i.name)",
            "CREATE INDEX code_name IF NOT EXISTS FOR (c:Code) ON (c.name)",
            "CREATE INDEX theme_name IF NOT EXISTS FOR (t:Theme) ON (t.name)"
        ]
        
        async with self.driver.session() as session:
            for query in schema_queries:
                try:
                    await session.run(query)
                except ClientError as e:
                    # Ignore if constraint/index already exists
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Schema creation warning: {e}")
        
        logger.info("Neo4j schema created successfully")
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get information about current schema."""
        if not self.is_connected:
            raise Neo4jConnectionError("Not connected to Neo4j")
        
        async with self.driver.session() as session:
            # Get node labels
            result = await session.run("CALL db.labels()")
            labels = [record["label"] async for record in result]
            
            # Get relationship types
            result = await session.run("CALL db.relationshipTypes()")
            rel_types = [record["relationshipType"] async for record in result]
            
            return {
                "node_labels": labels,
                "relationship_types": rel_types
            }
    
    async def store_global_result(self, result: GlobalCodingResult) -> str:
        """Store GlobalCodingResult in Neo4j graph."""
        if not self.is_connected:
            raise Neo4jConnectionError("Not connected to Neo4j")
        
        async with self.driver.session() as session:
            tx = await session.begin_transaction()
            try:
                # Create study node
                study_query = """
                CREATE (s:Study {
                    study_id: $study_id,
                    analysis_timestamp: $timestamp,
                    research_question: $research_question,
                    interviews_analyzed: $interviews_analyzed,
                    total_tokens_analyzed: $total_tokens_analyzed
                })
                RETURN s.study_id as study_id
                """
                
                study_result = await tx.run(study_query, {
                    'study_id': result.study_id,
                    'timestamp': result.analysis_timestamp.isoformat(),
                    'research_question': result.research_question,
                    'interviews_analyzed': result.interviews_analyzed,
                    'total_tokens_analyzed': result.total_tokens_analyzed
                })
                
                record = await study_result.single()
                study_id = record['study_id']
                
                # Store themes, codes, etc. (basic implementation)
                # TODO: Implement full graph structure in REFACTOR phase
                
                await tx.commit()
            except Exception:
                await tx.rollback()
                raise
                
        logger.info(f"Stored global result with ID: {study_id}")
        return study_id
    
    async def store_enhanced_result(self, result: EnhancedResult) -> str:
        """Store EnhancedResult with full traceability."""
        # First store the global analysis
        study_id = await self.store_global_result(result.global_analysis)
        
        # Then store enhanced data
        async with self.driver.session() as session:
            tx = await session.begin_transaction()
            try:
                # Store traceability metrics
                metrics_query = """
                MATCH (s:Study {study_id: $study_id})
                SET s.traceability_completeness = $traceability_completeness,
                    s.quote_chain_coverage = $quote_chain_coverage,
                    s.stakeholder_coverage = $stakeholder_coverage,
                    s.evidence_strength = $evidence_strength
                """
                
                await tx.run(metrics_query, {
                    'study_id': study_id,
                    'traceability_completeness': result.traceability_completeness,
                    'quote_chain_coverage': result.quote_chain_coverage,
                    'stakeholder_coverage': result.stakeholder_coverage,
                    'evidence_strength': result.evidence_strength
                })
                
                await tx.commit()
            except Exception:
                await tx.rollback()
                raise
        
        return study_id
    
    async def get_themes_by_prevalence(self, min_prevalence: float = 0.0) -> List[Dict[str, Any]]:
        """Query themes ordered by prevalence."""
        if not self.is_connected:
            raise Neo4jConnectionError("Not connected to Neo4j")
        
        query = """
        MATCH (t:Theme)
        WHERE t.prevalence >= $min_prevalence
        RETURN t.theme_id as theme_id, t.name as name, t.prevalence as prevalence
        ORDER BY t.prevalence DESC
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {'min_prevalence': min_prevalence})
            return [dict(record) async for record in result]
    
    async def get_quote_chains_for_theme(self, theme_id: str) -> List[Dict[str, Any]]:
        """Get quote chains for a specific theme."""
        if not self.is_connected:
            raise Neo4jConnectionError("Not connected to Neo4j")
        
        query = """
        MATCH (t:Theme {theme_id: $theme_id})-[:HAS_CHAIN]->(qc:QuoteChain)
        RETURN qc.chain_id as chain_id, qc.chain_type as chain_type, 
               qc.quotes_sequence as quotes_sequence
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {'theme_id': theme_id})
            return [dict(record) async for record in result]
    
    async def get_code_progressions(self, code_id: str) -> Dict[str, Any]:
        """Get how a code evolved across interviews."""
        if not self.is_connected:
            raise Neo4jConnectionError("Not connected to Neo4j")
        
        query = """
        MATCH (c:Code {code_id: $code_id})-[:HAS_PROGRESSION]->(cp:CodeProgression)
        RETURN cp.code_id as code_id, cp.progression_type as progression_type,
               cp.timeline as timeline
        LIMIT 1
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {'code_id': code_id})
            record = await result.single()
            return dict(record) if record else {}
    
    async def get_contradictions_for_theme(self, theme_id: str) -> List[Dict[str, Any]]:
        """Get contradictions within a theme."""
        if not self.is_connected:
            raise Neo4jConnectionError("Not connected to Neo4j")
        
        query = """
        MATCH (t:Theme {theme_id: $theme_id})-[:HAS_CONTRADICTION]->(con:Contradiction)
        RETURN con.contradiction_id as contradiction_id, con.position_a as position_a,
               con.position_b as position_b, con.evidence_a as evidence_a,
               con.evidence_b as evidence_b
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {'theme_id': theme_id})
            return [dict(record) async for record in result]
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute arbitrary Cypher query."""
        if not self.is_connected:
            raise Neo4jConnectionError("Not connected to Neo4j")
        
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            return [dict(record) async for record in result]
    
    def transaction(self):
        """Get transaction context for batch operations.""" 
        if not self.is_connected:
            raise Neo4jConnectionError("Not connected to Neo4j")
        
        return self.driver.session().begin_transaction()


# Async context manager for automatic cleanup
class Neo4jConnection:
    """Async context manager for Neo4j connections."""
    
    def __init__(self, uri: str = None, username: str = None, password: str = None):
        self.client = SimpleNeo4jClient(uri, username, password)
    
    async def __aenter__(self):
        await self.client.connect()
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()