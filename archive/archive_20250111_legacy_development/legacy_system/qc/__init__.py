"""
Qualitative Coding Analysis Tool

A comprehensive system for extracting entities, relationships, and thematic codes
from qualitative interview data using Neo4j and LLM integration.
"""

__version__ = "2.1.0"
__author__ = "Your Name"

# Import main components for easier access
from .core.llm_client import UniversalModelClient
from .core.neo4j_manager import EnhancedNeo4jManager
from .core.schema_config import SchemaConfiguration, create_research_schema
from .extraction.multi_pass_extractor import MultiPassExtractor, InterviewContext
from .query.cypher_builder import CypherQueryBuilder, NaturalLanguageParser

__all__ = [
    "UniversalModelClient",
    "EnhancedNeo4jManager", 
    "SchemaConfiguration",
    "create_research_schema",
    "MultiPassExtractor",
    "InterviewContext",
    "CypherQueryBuilder",
    "NaturalLanguageParser",
]