"""
Bridge module for core functionality
"""

from .neo4j_manager import EnhancedNeo4jManager, EntityNode, RelationshipEdge

__all__ = ['EnhancedNeo4jManager', 'EntityNode', 'RelationshipEdge']