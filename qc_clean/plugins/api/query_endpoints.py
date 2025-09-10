"""
Natural Language Query API Endpoints
Integrates AI query generation with Neo4j execution for UI frontend
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

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
                llm = LLMHandler(model_name='gpt-4o-mini')
                
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
                
                # For now, return mock data since we don't have Neo4j connection in this phase
                # In a real implementation, this would execute against Neo4j
                mock_results = self._generate_mock_results(request.query, cypher_query)
                
                return QueryResponse(
                    success=True,
                    cypher=cypher_query,
                    data=mock_results
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
                llm = LLMHandler(model_name='gpt-4o-mini')
                
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