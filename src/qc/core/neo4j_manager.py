"""
Bridge import for Neo4j Manager
Redirects to current qc_clean infrastructure
"""

import sys
from pathlib import Path

# Add the project root to the path for qc_clean imports
# Go up from src/qc/core/ to project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Bridge import to current system
from qc_clean.core.data.neo4j_manager import EnhancedNeo4jManager, EntityNode, RelationshipEdge

# Export for compatibility
__all__ = ['EnhancedNeo4jManager', 'EntityNode', 'RelationshipEdge']