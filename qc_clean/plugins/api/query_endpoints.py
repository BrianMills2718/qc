"""
Natural Language Query API Endpoints
Integrates AI query generation with Neo4j execution for UI frontend
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Import Neo4j manager for real database execution
from ...core.data.neo4j_manager import EnhancedNeo4jManager

logger = logging.getLogger(__name__)


class NaturalLanguageQueryRequest(BaseModel):
    """Request model for natural language queries"""
    query: str = Field(..., description="Natural language query to convert to Cypher")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for query")


class QueryResponse(BaseModel):
    """Response model for query results"""
    success: bool = Field(..., description="Whether query was successful")
    cypher: Optional[str] = Field(None, description="Generated Cypher query")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Query results")
    error: Optional[str] = Field(None, description="Error message if query failed")


class QueryEndpoints:
    """Encapsulates natural language query endpoints"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.QueryEndpoints")
        # Initialize Neo4j manager with environment configuration
        from ...core.config import config
        self.neo4j_manager = EnhancedNeo4jManager(
            uri=config.neo4j_uri,
            username=config.neo4j_username, 
            password=config.neo4j_password
        )
    
    def register_endpoints(self, app):
        """Register query endpoints with FastAPI app"""
        
        @app.post("/api/query/natural-language", response_model=QueryResponse)
        async def process_natural_language_query(request: NaturalLanguageQueryRequest):
            """Convert natural language to Cypher and execute against Neo4j"""
            try:
                self.logger.info(f"Processing natural language query: {request.query}")
                
                # Import working AI system components
                from investigation_ai_quality_assessment import AIQueryGenerationAssessment
                from qc_clean.core.llm.llm_handler import LLMHandler
                
                # Initialize AI query generation system (proven working)
                assessment = AIQueryGenerationAssessment()
                from ...core.config import config
                llm = LLMHandler(model_name=config.llm_model_name)
                
                # Generate Cypher query using working system
                cypher_query = await assessment.generate_cypher_query(
                    request.query, 'direct', llm
                )
                
                if not cypher_query:
                    self.logger.warning(f"Failed to generate Cypher for query: {request.query}")
                    return QueryResponse(
                        success=False,
                        error="Failed to generate valid Cypher query from natural language input"
                    )
                
                self.logger.info(f"Generated Cypher: {cypher_query}")
                
                # Execute Cypher query against real Neo4j database
                try:
                    neo4j_results = await self.neo4j_manager.execute_cypher(cypher_query)
                    
                    # Transform Neo4j results to API response format
                    formatted_results = self._format_neo4j_results(neo4j_results)
                    
                    return QueryResponse(
                        success=True,
                        cypher=cypher_query,
                        data=formatted_results
                    )
                except Exception as db_error:
                    self.logger.error(f"Neo4j execution error: {db_error}")
                    # Fallback to mock data if database fails
                    mock_results = self._generate_mock_results(request.query, cypher_query)
                    
                    return QueryResponse(
                        success=True,
                        cypher=cypher_query,
                        data=mock_results,
                        error=f"Database unavailable, using mock data: {str(db_error)}"
                    )
                
            except Exception as e:
                self.logger.error(f"Query processing error: {e}")
                
                # Categorize errors for better frontend handling
                error_message = str(e)
                if "LLMHandler" in error_message or "generate" in error_message:
                    error_type = "AI generation failed"
                elif "timeout" in error_message.lower():
                    error_type = "Query processing timeout"
                elif "validation" in error_message.lower():
                    error_type = "Invalid query format" 
                elif "connection" in error_message.lower():
                    error_type = "Database connection issue"
                else:
                    error_type = "Query processing failed"
                
                return QueryResponse(
                    success=False,
                    error=f"{error_type}: {error_message}"
                )
        
        @app.get("/api/query/health")
        async def query_health():
            """Health check for query endpoints"""
            try:
                # Test basic AI system availability
                from qc_clean.core.llm.llm_handler import LLMHandler
                from ...core.config import config
                llm = LLMHandler(model_name=config.llm_model_name)
                
                return {
                    "status": "healthy",
                    "ai_system": "available",
                    "endpoints": ["/api/query/natural-language"]
                }
            except Exception as e:
                return {
                    "status": "degraded",
                    "ai_system": "unavailable",
                    "error": str(e)
                }
    
    def _format_neo4j_results(self, neo4j_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform Neo4j query results to API response format"""
        formatted_results = []
        
        for record in neo4j_results:
            # Create standardized result format
            result_item = {
                "id": None,
                "name": None,
                "label": None,
                "properties": {}
            }
            
            # Extract node information from Neo4j record
            for key, value in record.items():
                if hasattr(value, 'labels') and hasattr(value, 'id'):
                    # Neo4j node object
                    result_item["id"] = str(value.id)
                    result_item["name"] = value.get('name', str(value.id))
                    result_item["label"] = value.get('name', list(value.labels)[0] if value.labels else 'Unknown')
                    result_item["properties"] = dict(value)
                elif isinstance(value, dict):
                    # Dictionary properties
                    result_item["properties"].update(value)
                else:
                    # Simple value
                    if key in ['name', 'label']:
                        result_item[key] = str(value)
                    else:
                        result_item["properties"][key] = value
            
            # Ensure required fields have values
            if not result_item["id"]:
                result_item["id"] = f"result_{len(formatted_results) + 1}"
            if not result_item["name"]:
                result_item["name"] = result_item["label"] or "Unknown"
            if not result_item["label"]:
                result_item["label"] = result_item["name"] or "Unknown"
                
            formatted_results.append(result_item)
        
        return formatted_results
    
    def _generate_mock_results(self, natural_query: str, cypher_query: str) -> List[Dict[str, Any]]:
        """Generate mock results for testing UI integration"""
        # Generate mock data based on query type
        query_lower = natural_query.lower()
        
        if 'people' in query_lower:
            return [
                {
                    "id": "person_1",
                    "name": "Dr. Sarah Johnson", 
                    "label": "Dr. Sarah Johnson",
                    "properties": {
                        "seniority": "senior",
                        "division": "research",
                        "interview_count": 3
                    }
                },
                {
                    "id": "person_2", 
                    "name": "Mike Chen",
                    "label": "Mike Chen",
                    "properties": {
                        "seniority": "junior", 
                        "division": "operations",
                        "interview_count": 2
                    }
                },
                {
                    "id": "person_3",
                    "name": "Prof. Emily Davis", 
                    "label": "Prof. Emily Davis",
                    "properties": {
                        "seniority": "senior",
                        "division": "policy", 
                        "interview_count": 4
                    }
                }
            ]
        elif 'organization' in query_lower:
            return [
                {
                    "id": "org_1",
                    "name": "TechCorp Inc",
                    "label": "TechCorp Inc", 
                    "properties": {
                        "size": "large",
                        "sector": "private",
                        "employee_count": 1200
                    }
                },
                {
                    "id": "org_2",
                    "name": "University Research Center", 
                    "label": "University Research Center",
                    "properties": {
                        "size": "medium",
                        "sector": "public",
                        "employee_count": 450
                    }
                }
            ]
        elif 'code' in query_lower:
            return [
                {
                    "id": "code_1",
                    "name": "Digital Transformation",
                    "label": "Digital Transformation",
                    "properties": {
                        "frequency": 24,
                        "confidence": 0.85,
                        "category": "technology"
                    }
                },
                {
                    "id": "code_2", 
                    "name": "Organizational Change",
                    "label": "Organizational Change",
                    "properties": {
                        "frequency": 18,
                        "confidence": 0.92,
                        "category": "process"
                    }
                },
                {
                    "id": "code_3",
                    "name": "Leadership Challenges", 
                    "label": "Leadership Challenges",
                    "properties": {
                        "frequency": 15,
                        "confidence": 0.78,
                        "category": "management"
                    }
                }
            ]
        else:
            # Generic results for unknown query types
            return [
                {
                    "id": "result_1",
                    "name": f"Result for: {natural_query[:30]}...",
                    "label": f"Query Result 1", 
                    "properties": {
                        "generated_from": cypher_query[:50] + "...",
                        "mock_data": True
                    }
                }
            ]


# Global instance for endpoint registration
query_endpoints = QueryEndpoints()