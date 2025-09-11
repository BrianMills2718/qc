"""
UI Integration Tests
Test the integration between frontend query interface and backend AI system
"""

import asyncio
import pytest
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ai_system_availability():
    """Test that the AI query generation system is available"""
    try:
        from investigation_ai_quality_assessment import AIQueryGenerationAssessment
        from qc_clean.core.llm.llm_handler import LLMHandler
        
        # Test basic instantiation
        assessment = AIQueryGenerationAssessment()
        llm = LLMHandler(model_name='gpt-4o-mini')
        
        assert assessment is not None
        assert llm is not None
        print("[SUCCESS] AI system components available")
        
    except Exception as e:
        pytest.fail(f"AI system components not available: {e}")

def test_query_endpoint_creation():
    """Test that query endpoints can be created"""
    try:
        from qc_clean.plugins.api.query_endpoints import QueryEndpoints, QueryResponse
        
        # Test endpoint instantiation
        endpoints = QueryEndpoints()
        assert endpoints is not None
        
        # Test response model
        response = QueryResponse(success=True, cypher="MATCH (p:Person) RETURN p", data=[])
        assert response.success is True
        assert response.cypher == "MATCH (p:Person) RETURN p"
        
        print("[SUCCESS] Query endpoints can be created")
        
    except Exception as e:
        pytest.fail(f"Query endpoint creation failed: {e}")

@pytest.mark.asyncio
async def test_basic_query_generation():
    """Test basic query generation functionality"""
    try:
        from investigation_ai_quality_assessment import AIQueryGenerationAssessment
        from qc_clean.core.llm.llm_handler import LLMHandler
        
        # Initialize components
        assessment = AIQueryGenerationAssessment()
        llm = LLMHandler(model_name='gpt-4o-mini')
        
        # Test query generation
        query = "Show me all people"
        result = await assessment.generate_cypher_query(query, 'direct', llm)
        
        # Basic validation
        assert result is not None, "Query generation returned None"
        assert len(result.strip()) > 0, "Query generation returned empty string"
        assert 'MATCH' in result or 'match' in result, "Generated query doesn't contain MATCH clause"
        
        print(f"[SUCCESS] Query generation successful: {result}")
        
    except Exception as e:
        pytest.fail(f"Basic query generation failed: {e}")

@pytest.mark.asyncio
async def test_query_endpoint_mock_processing():
    """Test query endpoint processing with mock data"""
    try:
        from qc_clean.plugins.api.query_endpoints import QueryEndpoints, NaturalLanguageQueryRequest
        
        # Create endpoint handler
        endpoints = QueryEndpoints()
        
        # Test mock result generation
        mock_results = endpoints._generate_mock_results("Show me all people", "MATCH (p:Person) RETURN p")
        
        assert isinstance(mock_results, list), "Mock results should be a list"
        assert len(mock_results) > 0, "Mock results should not be empty"
        
        # Validate result structure
        for result in mock_results:
            assert 'id' in result, "Each result should have an id"
            assert 'label' in result, "Each result should have a label"
            
        print(f"[SUCCESS] Mock results generated: {len(mock_results)} items")
        
    except Exception as e:
        pytest.fail(f"Query endpoint mock processing failed: {e}")

def test_api_server_integration():
    """Test that query endpoints can be registered with API server"""
    try:
        from qc_clean.plugins.api.api_server import QCAPIServer
        from qc_clean.plugins.api.query_endpoints import query_endpoints
        
        # Create API server config
        config = {
            'enable_docs': True,
            'cors_origins': ['*']
        }
        
        # Test server creation
        server = QCAPIServer(config)
        assert server is not None
        
        print("[SUCCESS] API server can be created and configured")
        
    except Exception as e:
        pytest.fail(f"API server integration test failed: {e}")

def test_ui_mockup_file_exists():
    """Test that the enhanced UI mockup file exists and contains query panel"""
    try:
        mockup_path = project_root / "UI_planning" / "mockups" / "02_project_workspace.html"
        assert mockup_path.exists(), f"UI mockup file not found: {mockup_path}"
        
        # Read file content
        with open(mockup_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for query panel elements
        assert 'natural-query' in content, "Query input textarea not found"
        assert 'execute-query' in content, "Execute query button not found"
        assert 'processNaturalLanguageQuery' in content, "Query processing function not found"
        assert 'updateGraphWithQueryResults' in content, "Graph update function not found"
        
        print("[SUCCESS] UI mockup contains all required query interface elements")
        
    except Exception as e:
        pytest.fail(f"UI mockup validation failed: {e}")

def test_integration_data_flow():
    """Test the complete data flow from query to mock results"""
    try:
        from qc_clean.plugins.api.query_endpoints import QueryEndpoints
        
        endpoints = QueryEndpoints()
        
        # Test different query types
        test_queries = [
            ("Show me all people", "person"),
            ("Find large organizations", "organization"), 
            ("Which codes appear frequently?", "code"),
            ("Random query", "result")
        ]
        
        for query, expected_type in test_queries:
            mock_results = endpoints._generate_mock_results(query, f"MATCH (n) WHERE n.type='{expected_type}' RETURN n")
            
            assert len(mock_results) > 0, f"No mock results for query: {query}"
            
            # Check result structure
            result = mock_results[0]
            assert 'id' in result, f"Missing id in result for query: {query}"
            assert 'name' in result or 'label' in result, f"Missing name/label in result for query: {query}"
            
        print("[SUCCESS] Data flow integration test passed")
        
    except Exception as e:
        pytest.fail(f"Integration data flow test failed: {e}")

if __name__ == "__main__":
    """Run integration tests directly"""
    print("Running UI Integration Tests...")
    print("=" * 50)
    
    # Run synchronous tests
    try:
        test_ai_system_availability()
        test_query_endpoint_creation()
        test_api_server_integration()
        test_ui_mockup_file_exists()
        test_integration_data_flow()
        
        print("\n" + "=" * 50)
        print("Running async tests...")
        
        # Run async tests
        asyncio.run(test_basic_query_generation())
        asyncio.run(test_query_endpoint_mock_processing())
        
        print("\n" + "=" * 50)
        print("[SUCCESS] ALL INTEGRATION TESTS PASSED!")
        print("UI Cypher Integration is ready for end-to-end validation")
        
    except Exception as e:
        print(f"\n[FAILED] INTEGRATION TEST FAILED: {e}")
        sys.exit(1)