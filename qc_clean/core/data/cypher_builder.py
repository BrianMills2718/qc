"""
Cypher Query Builder for Natural Language Queries

This module converts natural language questions into Cypher queries that can
be executed against the Neo4j graph database to extract insights about
entities, relationships, and codes.

Examples:
- "What do senior people say about AI?" 
- "Which organizations mention innovation?"
- "How do large companies view automation?"
- "Show relationships between people and methods"
"""

import asyncio
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .schema_config import SchemaConfiguration, PropertyType
from ..utils.error_handler import QueryError

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries the system can handle"""
    ENTITY_PROPERTY_FILTER = "entity_property_filter"  # "senior people", "large organizations"
    ENTITY_CODE_RELATIONSHIP = "entity_code_relationship"  # "what do X say about Y"
    ENTITY_ENTITY_RELATIONSHIP = "entity_entity_relationship"  # "which people work at organizations"
    CODE_ANALYSIS = "code_analysis"  # "most common codes", "code frequency"
    AGGREGATION = "aggregation"  # "count of X", "distribution of Y"
    CENTRALITY = "centrality"  # "most connected entities"


@dataclass
class QueryIntent:
    """Parsed intent from natural language query"""
    query_type: QueryType
    target_entities: List[str]  # Entity types being queried
    filters: Dict[str, Any]  # Property filters (e.g., seniority="senior")
    relationships: List[str]  # Relationship types involved
    codes: List[str]  # Code names mentioned
    aggregation: Optional[str] = None  # count, avg, sum, etc.
    limit: Optional[int] = None
    order_by: Optional[str] = None


@dataclass
class CypherQuery:
    """Generated Cypher query with metadata"""
    cypher: str
    parameters: Dict[str, Any]
    description: str
    estimated_complexity: str  # "low", "medium", "high"
    expected_result_type: str  # "entities", "relationships", "counts", "insights"


@dataclass
class QueryResult:
    """Formatted query results with metadata"""
    success: bool
    results: List[Dict[str, Any]]
    result_count: int
    query_time_ms: float
    description: str
    result_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class NaturalLanguageParser:
    """Parses natural language queries into structured intents"""
    
    def __init__(self, schema: SchemaConfiguration, entity_aliases: Optional[Dict[str, str]] = None):
        self.schema = schema
        self.entity_aliases = entity_aliases or {}
        self._build_vocabularies()
    
    def _build_vocabularies(self):
        """Build vocabularies for entity types, properties, and relationships"""
        self.entity_types = set(self.schema.entities.keys())
        self.entity_names = list(self.schema.entities.keys())  # Add entity_names attribute
        
        # Build default aliases if not provided
        if not self.entity_aliases:
            self._build_default_aliases()
        
    def _build_default_aliases(self):
        """Build default entity aliases from schema"""
        for entity_type in self.entity_types:
            # Add lowercase version
            self.entity_aliases[entity_type.lower()] = entity_type
            
            # Add plural version (simple 's' suffix)
            plural = entity_type.lower() + "s"
            if not plural.endswith("ss"):  # Avoid double 's'
                self.entity_aliases[plural] = entity_type
            
            # Add common variations based on entity description
            entity_config = self.schema.entities.get(entity_type)
            description = getattr(entity_config, "description", "") or ""
            description = description.lower()
            
            # Extract potential aliases from description
            # e.g., "Research methods and approaches" -> ["methods", "approaches"]
            import re
            words = re.findall(r'\b\w+\b', description)
            for word in words:
                if len(word) > 3 and word not in ["and", "the", "with", "for"]:
                    self.entity_aliases[word] = entity_type
        
        # Build property vocabularies
        self.properties = {}
        self.property_values = {}
        
        for entity_type, entity_def in self.schema.entities.items():
            for prop_name, prop_def in entity_def.properties.items():
                key = f"{entity_type.lower()}_{prop_name}"
                self.properties[key] = (entity_type, prop_name)
                
                # Store enum values for matching
                if prop_def.type == PropertyType.ENUM and prop_def.values:
                    self.property_values[prop_name] = prop_def.values
        
        # Build relationship vocabulary
        self.relationships = {}
        for entity_type, entity_def in self.schema.entities.items():
            for rel_name, rel_def in entity_def.relationships.items():
                self.relationships[rel_def.relationship_type] = {
                    "source": entity_type,
                    "target": rel_def.target_entity,
                    "type": rel_def.relationship_type
                }
    
    def parse_query(self, query: str) -> QueryIntent:
        """Parse natural language query into structured intent"""
        query = query.lower().strip()
        logger.info(f"Parsing query: {query}")
        
        # Determine query type
        query_type = self._classify_query_type(query)
        
        # Extract entities
        target_entities = self._extract_entities(query)
        
        # Extract filters
        filters = self._extract_filters(query)
        
        # Extract relationships
        relationships = self._extract_relationships(query)
        
        # Extract codes
        codes = self._extract_codes(query)
        
        # Extract aggregation and ordering
        aggregation = self._extract_aggregation(query)
        limit = self._extract_limit(query)
        order_by = self._extract_ordering(query)
        
        intent = QueryIntent(
            query_type=query_type,
            target_entities=target_entities,
            filters=filters,
            relationships=relationships,
            codes=codes,
            aggregation=aggregation,
            limit=limit,
            order_by=order_by
        )
        
        logger.info(f"Parsed intent: {intent}")
        return intent
    
    def _classify_query_type(self, query: str) -> QueryType:
        """Classify the type of query based on patterns"""
        
        # Code analysis patterns (check FIRST to catch "most common codes")
        if any(pattern in query for pattern in [
            "codes", "themes", "topics", "patterns"
        ]) or ("most common" in query and ("code" in query or "theme" in query)):
            return QueryType.CODE_ANALYSIS
        
        # Entity-code relationship patterns
        if any(pattern in query for pattern in [
            "what do", "what does", "how do", "how does", 
            "say about", "think about", "mention", "discuss"
        ]):
            return QueryType.ENTITY_CODE_RELATIONSHIP
        
        # Entity-entity relationship patterns
        if any(pattern in query for pattern in [
            "who works", "which people", "what organizations", 
            "relationships between", "connections between"
        ]):
            return QueryType.ENTITY_ENTITY_RELATIONSHIP
        
        # Centrality patterns (check before aggregation to catch "most connected")
        if any(pattern in query for pattern in [
            "most connected", "central", "influential", "important"
        ]):
            return QueryType.CENTRALITY
        
        # Aggregation patterns
        if any(pattern in query for pattern in [
            "count", "how many", "number of", "total", 
            "distribution", "frequency", "most common"
        ]):
            return QueryType.AGGREGATION
        
        # Default to entity property filter
        return QueryType.ENTITY_PROPERTY_FILTER
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract entity types mentioned in the query"""
        entities = []
        
        # Direct entity type matches
        for entity_type in self.entity_types:
            if entity_type.lower() in query:
                entities.append(entity_type)
        
        # Alias matches
        for alias, entity_type in self.entity_aliases.items():
            if alias in query:
                entities.append(entity_type)
        
        return list(set(entities))  # Remove duplicates
    
    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract property filters from the query"""
        filters = {}
        
        # Look for property value patterns
        for prop_name, values in self.property_values.items():
            for value in values:
                if value in query:
                    filters[prop_name] = value
        
        # Look for specific patterns
        patterns = [
            (r"senior (people|staff|researchers)", {"seniority": "senior"}),
            (r"junior (people|staff|researchers)", {"seniority": "junior"}),
            (r"large (organizations|companies)", {"size": "large"}),
            (r"small (organizations|companies)", {"size": "small"}),
            (r"medium (organizations|companies)", {"size": "medium"}),
            (r"public (organizations|companies)", {"sector": "public"}),
            (r"private (organizations|companies)", {"sector": "private"}),
            (r"qualitative methods", {"method_type": "qualitative"}),
            (r"quantitative methods", {"method_type": "quantitative"})
        ]
        
        for pattern, filter_dict in patterns:
            if re.search(pattern, query):
                filters.update(filter_dict)
        
        return filters
    
    def _extract_relationships(self, query: str) -> List[str]:
        """Extract relationship types from the query"""
        relationships = []
        
        # Pattern matching for relationships
        patterns = [
            (r"work(s)? at", "WORKS_AT"),
            (r"employed (at|by)", "WORKS_AT"),
            (r"manage(s)?", "MANAGES"),
            (r"collaborat(e|es|ing) with", "COLLABORATES_WITH"),
            (r"partner(s)? with", "COLLABORATES_WITH")
        ]
        
        for pattern, rel_type in patterns:
            if re.search(pattern, query):
                relationships.append(rel_type)
        
        return relationships
    
    def _extract_codes(self, query: str) -> List[str]:
        """Extract code/theme mentions from the query"""
        codes = []
        
        # Common code patterns
        code_patterns = [
            "ai", "artificial intelligence", "automation", "machine learning",
            "innovation", "efficiency", "adoption", "challenges", "barriers",
            "success", "failure", "methodology", "analysis", "research"
        ]
        
        for pattern in code_patterns:
            if pattern in query:
                # Convert to likely code name format
                code_name = pattern.replace(" ", "_").replace("-", "_")
                codes.append(code_name)
        
        return codes
    
    def _extract_aggregation(self, query: str) -> Optional[str]:
        """Extract aggregation type from query"""
        if any(word in query for word in ["count", "how many", "number"]):
            return "count"
        elif any(word in query for word in ["average", "avg", "mean"]):
            return "avg"
        elif "total" in query:
            return "sum"
        elif any(word in query for word in ["distribution", "breakdown"]):
            return "group"
        return None
    
    def _extract_limit(self, query: str) -> Optional[int]:
        """Extract limit from query"""
        # Look for patterns like "top 10", "first 5", "show 3"
        patterns = [
            r"top (\d+)",
            r"first (\d+)", 
            r"show (\d+)",
            r"limit (\d+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_ordering(self, query: str) -> Optional[str]:
        """Extract ordering preferences from query"""
        if any(word in query for word in ["most", "highest", "top"]):
            return "DESC"
        elif any(word in query for word in ["least", "lowest", "bottom"]):
            return "ASC"
        return None


class CypherQueryBuilder:
    """Builds Cypher queries from parsed intents"""
    
    def __init__(self, neo4j_manager, parser):
        self.neo4j = neo4j_manager
        self.parser = parser
        self.schema = parser.schema if hasattr(parser, 'schema') else None
    
    async def execute_natural_language_query(self, natural_language_query: str) -> QueryResult:
        """Execute a natural language query and return formatted results"""
        try:
            # Parse the query
            intent = self.parser.parse_query(natural_language_query)
            
            # Build Cypher query
            cypher_query = self.build_query(intent)
            
            # Execute query
            import time
            start_time = time.time()
            results = await self.neo4j.execute_cypher(
                cypher_query.cypher, 
                cypher_query.parameters
            )
            query_time_ms = (time.time() - start_time) * 1000
            
            # Format results
            formatter = ResultFormatter()
            formatted_result = formatter.format_results(
                results, 
                cypher_query.expected_result_type,
                intent
            )
            formatted_result.query_time_ms = query_time_ms
            formatted_result.description = cypher_query.description
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryError(f"Cypher query execution failed: {e}") from e
    
    def build_query(self, intent: QueryIntent) -> CypherQuery:
        """Build Cypher query from parsed intent"""
        
        if intent.query_type == QueryType.ENTITY_CODE_RELATIONSHIP:
            return self._build_entity_code_query(intent)
        elif intent.query_type == QueryType.ENTITY_ENTITY_RELATIONSHIP:
            return self._build_entity_relationship_query(intent)
        elif intent.query_type == QueryType.AGGREGATION:
            return self._build_aggregation_query(intent)
        elif intent.query_type == QueryType.CENTRALITY:
            return self._build_centrality_query(intent)
        elif intent.query_type == QueryType.CODE_ANALYSIS:
            return self._build_code_analysis_query(intent)
        else:  # ENTITY_PROPERTY_FILTER
            return self._build_entity_filter_query(intent)
    
    def _build_entity_code_query(self, intent: QueryIntent) -> CypherQuery:
        """Build query for entity-code relationships using quote-centric architecture"""
        
        where_clauses = []
        params = {}
        
        # Entity type filter
        if intent.target_entities:
            entity_types = intent.target_entities
            where_clauses.append("e.entity_type IN $entity_types")
            params["entity_types"] = entity_types
        
        # Property filters
        for prop, value in intent.filters.items():
            param_name = f"filter_{prop}"
            where_clauses.append(f"e.{prop} = ${param_name}")
            params[param_name] = value
        
        # Code filters (if specific codes mentioned)
        if intent.codes:
            where_clauses.append("c.name IN $codes")
            params["codes"] = intent.codes
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Quote-centric query: Find entities and codes connected through quotes
        cypher = f"""
        MATCH (e:Entity)<-[r1:MENTIONS]-(q:Quote)-[r2:SUPPORTS]->(c:Code)
        {where_clause}
        RETURN e.name as entity_name, 
               e.entity_type as entity_type,
               e as entity_properties,
               c.name as code_name,
               c.definition as code_definition,
               q.text as supporting_quote,
               q.line_start as quote_line_start,
               q.line_end as quote_line_end,
               q.interview_id as quote_interview,
               r1.confidence as mention_confidence,
               r2.confidence as support_confidence
        ORDER BY r2.confidence DESC, r1.confidence DESC, e.name
        """
        
        if intent.limit:
            cypher += f" LIMIT {intent.limit}"
        
        return CypherQuery(
            cypher=cypher.strip(),
            parameters=params,
            description=f"Find {', '.join(intent.target_entities) if intent.target_entities else 'entities'} that discuss {', '.join(intent.codes) if intent.codes else 'themes'} with quote evidence and filters: {intent.filters}",
            estimated_complexity="medium",
            expected_result_type="entity-code relationships with quotes"
        )
    
    def _build_entity_relationship_query(self, intent: QueryIntent) -> CypherQuery:
        """Build query for entity-entity relationships"""
        
        where_clauses = []
        params = {}
        
        # Entity type filters
        if intent.target_entities:
            if len(intent.target_entities) >= 2:
                where_clauses.append("e1.entity_type = $entity_type1 AND e2.entity_type = $entity_type2")
                params["entity_type1"] = intent.target_entities[0]
                params["entity_type2"] = intent.target_entities[1]
            else:
                where_clauses.append("(e1.entity_type = $entity_type OR e2.entity_type = $entity_type)")
                params["entity_type"] = intent.target_entities[0]
        
        # Property filters for source entities
        for prop, value in intent.filters.items():
            param_name = f"filter_{prop}"
            where_clauses.append(f"e1.{prop} = ${param_name}")
            params[param_name] = value
        
        # Relationship type filter
        rel_pattern = ""
        if intent.relationships:
            rel_types = "|".join(intent.relationships)
            rel_pattern = f"[r:{rel_types}]"
        else:
            rel_pattern = "[r]"
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        cypher = f"""
        MATCH (e1:Entity)-{rel_pattern}-(e2:Entity)
        {where_clause}
        RETURN e1.name as source_entity,
               e1.entity_type as source_type,
               type(r) as relationship_type,
               r as relationship_properties,
               e2.name as target_entity,
               e2.entity_type as target_type,
               e1 as source_properties,
               e2 as target_properties
        ORDER BY e1.name, e2.name
        """
        
        if intent.limit:
            cypher += f" LIMIT {intent.limit}"
        
        return CypherQuery(
            cypher=cypher.strip(),
            parameters=params,
            description=f"Find relationships between {', '.join(intent.target_entities) if intent.target_entities else 'entities'} with filters: {intent.filters}",
            estimated_complexity="medium",
            expected_result_type="entity relationships"
        )
    
    def _build_aggregation_query(self, intent: QueryIntent) -> CypherQuery:
        """Build aggregation query"""
        
        if intent.aggregation == "count":
            # Count entities by type or property
            group_by = "e.entity_type"
            if intent.filters:
                # Count by filtered property
                prop_name = list(intent.filters.keys())[0]
                group_by = f"e.{prop_name}"
            
            where_clauses = []
            params = {}
            
            if intent.target_entities:
                where_clauses.append("e.entity_type IN $entity_types")
                params["entity_types"] = intent.target_entities
            
            for prop, value in intent.filters.items():
                param_name = f"filter_{prop}"
                where_clauses.append(f"e.{prop} = ${param_name}")
                params[param_name] = value
            
            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            cypher = f"""
            MATCH (e:Entity)
            {where_clause}
            RETURN {group_by} as category,
                   count(e) as count
            ORDER BY count DESC
            """
            
            return CypherQuery(
                cypher=cypher.strip(),
                parameters=params,
                description=f"Count entities by {group_by} with filters: {intent.filters}",
                estimated_complexity="low",
                expected_result_type="counts"
            )
        
        # Default fallback
        return self._build_entity_filter_query(intent)
    
    def _build_centrality_query(self, intent: QueryIntent) -> CypherQuery:
        """Build centrality analysis query"""
        
        where_clauses = []
        params = {}
        
        if intent.target_entities:
            where_clauses.append("e.entity_type IN $entity_types")
            params["entity_types"] = intent.target_entities
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        cypher = f"""
        MATCH (e:Entity)
        {where_clause}
        OPTIONAL MATCH (e)-[r]-()
        WITH e, count(r) as degree
        RETURN e.name as entity_name,
               e.entity_type as entity_type,
               e as entity_properties,
               degree as connection_count
        ORDER BY degree DESC
        """
        
        if intent.limit:
            cypher += f" LIMIT {intent.limit}"
        
        return CypherQuery(
            cypher=cypher.strip(),
            parameters=params,
            description=f"Find most connected {', '.join(intent.target_entities) if intent.target_entities else 'entities'}",
            estimated_complexity="medium",
            expected_result_type="centrality analysis"
        )
    
    def _build_code_analysis_query(self, intent: QueryIntent) -> CypherQuery:
        """Build code analysis query"""
        
        cypher = """
        MATCH (c:Code)
        RETURN c.name as code_name,
               c.definition as code_definition,
               size(c.quotes) as quote_count,
               c.confidence as confidence
        ORDER BY quote_count DESC, confidence DESC
        """
        
        if intent.limit:
            cypher += f" LIMIT {intent.limit}"
        
        return CypherQuery(
            cypher=cypher.strip(),
            parameters={},
            description="Analyze codes by frequency and confidence",
            estimated_complexity="low",
            expected_result_type="code analysis"
        )
    
    def _build_entity_filter_query(self, intent: QueryIntent) -> CypherQuery:
        """Build basic entity filter query"""
        
        where_clauses = []
        params = {}
        
        if intent.target_entities:
            where_clauses.append("e.entity_type IN $entity_types")
            params["entity_types"] = intent.target_entities
        
        for prop, value in intent.filters.items():
            param_name = f"filter_{prop}"
            where_clauses.append(f"e.{prop} = ${param_name}")
            params[param_name] = value
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        cypher = f"""
        MATCH (e:Entity)
        {where_clause}
        RETURN e.name as entity_name,
               e.entity_type as entity_type,
               e as entity_properties
        ORDER BY e.name
        """
        
        if intent.limit:
            cypher += f" LIMIT {intent.limit}"
        
        return CypherQuery(
            cypher=cypher.strip(),
            parameters=params,
            description=f"Find {', '.join(intent.target_entities) if intent.target_entities else 'entities'} with filters: {intent.filters}",
            estimated_complexity="low",
            expected_result_type="filtered entities"
        )


class ResultFormatter:
    """Formats query results for human consumption"""
    
    @staticmethod
    def format_results(raw_results: List[Dict[str, Any]], 
                      query_type: str,
                      intent: QueryIntent) -> QueryResult:
        """Format raw Neo4j results into structured QueryResult"""
        
        formatted_results = []
        
        if query_type == "entities":
            # Format entity results
            for row in raw_results:
                entity = row.get('e', {})
                formatted_results.append({
                    'name': entity.get('name', 'Unknown'),
                    'type': entity.get('entity_type', 'Unknown'),
                    'properties': {k: v for k, v in entity.items() 
                                 if k not in ['name', 'entity_type', 'id']}
                })
        
        elif query_type == "relationships":
            # Format relationship results
            for row in raw_results:
                formatted_results.append({
                    'source': row.get('source', {}).get('name', 'Unknown'),
                    'target': row.get('target', {}).get('name', 'Unknown'),
                    'relationship': row.get('rel_type', 'Unknown'),
                    'properties': row.get('rel_props', {})
                })
        
        elif query_type == "counts":
            # Format aggregation results
            for row in raw_results:
                formatted_results.append({
                    'category': row.get('category', 'Total'),
                    'count': row.get('count', 0),
                    'percentage': row.get('percentage', 0)
                })
        
        elif query_type == "insights":
            # Format analysis results
            for row in raw_results:
                formatted_results.append({
                    'entity': row.get('entity', {}).get('name', 'Unknown'),
                    'metric': row.get('metric', 0),
                    'rank': row.get('rank', 0),
                    'details': row.get('details', {})
                })
        
        else:
            # Generic formatting
            formatted_results = raw_results
        
        return QueryResult(
            success=True,
            results=formatted_results,
            result_count=len(formatted_results),
            query_time_ms=0,  # Would be set by executor
            description=f"Found {len(formatted_results)} results",
            result_type=query_type,
            metadata={'intent': intent.__dict__}
        )


class NaturalLanguageQuerySystem:
    """Complete system for natural language to Cypher queries"""
    
    def __init__(self, schema: SchemaConfiguration, neo4j_manager, 
                 entity_aliases: Optional[Dict[str, str]] = None):
        self.schema = schema
        self.neo4j = neo4j_manager
        self.parser = NaturalLanguageParser(schema, entity_aliases)
        self.query_builder = CypherQueryBuilder(neo4j_manager, self.parser)
        self.formatter = ResultFormatter()
    
    async def query(self, natural_language_query: str) -> Dict[str, Any]:
        """Process natural language query and return results"""
        
        try:
            # Parse the query
            intent = self.parser.parse_query(natural_language_query)
            
            # Build Cypher query
            cypher_query = self.query_builder.build_query(intent)
            
            # Execute query
            import time
            start_time = time.time()
            results = await self.neo4j.execute_cypher(
                cypher_query.cypher, 
                cypher_query.parameters
            )
            query_time_ms = (time.time() - start_time) * 1000
            
            # Format results
            formatted_result = self.formatter.format_results(
                results, 
                cypher_query.expected_result_type,
                intent
            )
            formatted_result.query_time_ms = query_time_ms
            formatted_result.description = cypher_query.description
            
            return {
                "success": True,
                "query": natural_language_query,
                "intent": intent.__dict__,
                "cypher": cypher_query.cypher,
                "parameters": cypher_query.parameters,
                "description": cypher_query.description,
                "results": formatted_result.results,
                "result_count": formatted_result.result_count,
                "complexity": cypher_query.estimated_complexity,
                "query_time_ms": query_time_ms,
                "formatted_result": formatted_result
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise QueryError(f"Query processing failed: {e}") from e


# Test the query system
async def test_query_system():
    """Test the natural language query system"""
    print("🧪 Testing Natural Language Query System")
    print("=" * 60)
    
    from schema_config import create_research_schema
    from enhanced_neo4j_manager import EnhancedNeo4jManager, EntityNode, RelationshipEdge
    
    # Load schema
    schema = create_research_schema()
    
    # Initialize Neo4j
    neo4j = EnhancedNeo4jManager(
        uri="bolt://localhost:7687",
        username="neo4j", 
        password="qualitative123"
    )
    await neo4j.connect()
    
    # Create test data
    print("\n📝 Creating test data...")
    
    # Clean up any existing test data
    await neo4j.execute_cypher("""
        MATCH (e:Entity) WHERE e.test_data = true
        DETACH DELETE e
    """)
    
    # Create test entities
    senior_person = EntityNode(
        id="test_senior_001",
        name="Dr. Alice Smith",
        entity_type="Person",
        properties={
            "seniority": "senior",
            "division": "Methods Division",
            "test_data": True,
            "source_quotes": ["Dr. Smith mentioned AI adoption challenges"]
        }
    )
    
    junior_person = EntityNode(
        id="test_junior_001", 
        name="Bob Johnson",
        entity_type="Person",
        properties={
            "seniority": "junior",
            "division": "Policy Division", 
            "test_data": True,
            "source_quotes": ["Bob discussed automation benefits"]
        }
    )
    
    large_org = EntityNode(
        id="test_org_001",
        name="Tech Corp",
        entity_type="Organization",
        properties={
            "size": "large",
            "sector": "private",
            "test_data": True
        }
    )
    
    await neo4j.create_entity(senior_person)
    await neo4j.create_entity(junior_person)
    await neo4j.create_entity(large_org)
    
    # Create test codes
    await neo4j.create_code({
        'id': 'test_code_ai',
        'name': 'ai_adoption',
        'definition': 'Discussion about AI technology adoption',
        'quotes': ['Dr. Smith mentioned AI adoption challenges', 'AI tools are transforming research'],
        'confidence': 0.9,
        'session_id': 'test_session'
    })
    
    await neo4j.create_code({
        'id': 'test_code_auto',
        'name': 'automation',
        'definition': 'Discussion about automation benefits',
        'quotes': ['Bob discussed automation benefits', 'Automation improves efficiency'],
        'confidence': 0.85,
        'session_id': 'test_session'
    })
    
    print("✅ Test data created")
    
    # Initialize query system
    query_system = NaturalLanguageQuerySystem(schema, neo4j)
    
    # Test queries
    test_queries = [
        "What do senior people say about AI?",
        "How many people are there?",
        "Show me large organizations",
        "Which people work at organizations?",
        "What are the most common codes?",
        "Show top 3 most connected entities"
    ]
    
    print("\n🔍 Testing natural language queries...")
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        
        result = await query_system.query(query)
        
        if result["success"]:
            print(f"✅ Success: {result['description']}")
            print(f"📊 Results: {result['result_count']} items")
            print(f"🔧 Complexity: {result['complexity']}")
            
            # Show first few results
            if result["results"]:
                print("📋 Sample results:")
                for i, item in enumerate(result["results"][:2]):
                    print(f"  {i+1}. {item}")
        else:
            print(f"❌ Error: {result['error']}")
    
    # Clean up
    print("\n🧹 Cleaning up test data...")
    await neo4j.execute_cypher("""
        MATCH (e:Entity) WHERE e.test_data = true
        DETACH DELETE e
    """)
    await neo4j.execute_cypher("""
        MATCH (c:Code) WHERE c.id STARTS WITH 'test_'
        DELETE c
    """)
    print("✅ Cleaned up test data")
    
    await neo4j.close()
    print("\n🎉 Natural Language Query System test completed!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_query_system())