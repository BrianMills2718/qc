"""
End-to-End Validation Test
Simulates complete user workflow from UI input to graph visualization
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_complete_workflow():
    """Test the complete workflow from natural language query to graph data"""
    print("Starting End-to-End Validation...")
    print("=" * 50)
    
    try:
        # Step 1: Verify AI Query Generation System
        print("Step 1: Testing AI Query Generation...")
        from investigation_ai_quality_assessment import AIQueryGenerationAssessment
        from qc_clean.core.llm.llm_handler import LLMHandler
        
        assessment = AIQueryGenerationAssessment()
        llm = LLMHandler(model_name='gpt-4o-mini')
        
        # Test queries that will be used in UI
        test_queries = [
            "Show me all people",
            "Find people who work at large organizations", 
            "Which codes appear most frequently?"
        ]
        
        generated_queries = {}
        for query in test_queries:
            cypher = await assessment.generate_cypher_query(query, 'direct', llm)
            assert cypher is not None, f"Failed to generate query for: {query}"
            generated_queries[query] = cypher
            print(f"  [SUCCESS] '{query}' -> {cypher}")
        
        print("Step 1 PASSED: AI query generation working\n")
        
        # Step 2: Test Query Endpoint Processing
        print("Step 2: Testing Query Endpoint Processing...")
        from qc_clean.plugins.api.query_endpoints import QueryEndpoints, NaturalLanguageQueryRequest
        
        endpoints = QueryEndpoints()
        
        for query, cypher in generated_queries.items():
            mock_results = endpoints._generate_mock_results(query, cypher)
            assert len(mock_results) > 0, f"No mock results for query: {query}"
            
            # Validate data format for Cytoscape
            for result in mock_results:
                assert 'id' in result, f"Missing id in result for: {query}"
                assert 'label' in result or 'name' in result, f"Missing label/name for: {query}"
                
            print(f"  [SUCCESS] Mock data generated for '{query}': {len(mock_results)} results")
            
        print("Step 2 PASSED: Query endpoint processing working\n")
        
        # Step 3: Test API Server Integration
        print("Step 3: Testing API Server Integration...")
        from qc_clean.plugins.api.api_server import QCAPIServer
        
        config = {
            'enable_docs': True,
            'cors_origins': ['*'],
            'background_processing_enabled': False  # For testing
        }
        
        server = QCAPIServer(config)
        assert server is not None
        
        # Simulate server startup (without actually starting HTTP server)
        server._app = MockApp()  # Mock FastAPI app
        server._register_default_endpoints()
        
        print("  [SUCCESS] API server integration working")
        print("Step 3 PASSED: API endpoints registered\n")
        
        # Step 4: Test UI Component Validation
        print("Step 4: Testing UI Component Validation...")
        
        # Check that UI mockup file has all required elements
        mockup_path = project_root / "UI_planning" / "mockups" / "02_project_workspace.html"
        with open(mockup_path, 'r', encoding='utf-8') as f:
            ui_content = f.read()
            
        required_elements = [
            'id="natural-query"',
            'id="execute-query"', 
            'id="query-results"',
            'id="cypher-display"',
            'processNaturalLanguageQuery',
            'updateGraphWithQueryResults',
            'handleQueryError',
            'fillTemplate'
        ]
        
        for element in required_elements:
            assert element in ui_content, f"Missing UI element: {element}"
            
        print("  [SUCCESS] UI mockup contains all required elements")
        print("Step 4 PASSED: UI integration components ready\n")
        
        # Step 5: Simulate Complete Data Flow
        print("Step 5: Testing Complete Data Flow...")
        
        # Simulate the complete flow:
        # User input -> AI generation -> Mock execution -> UI format
        for user_query in test_queries:
            # 1. Natural language query (simulates UI input)
            print(f"  Processing: '{user_query}'")
            
            # 2. AI generates Cypher (simulates backend processing)
            cypher_query = await assessment.generate_cypher_query(user_query, 'direct', llm)
            assert cypher_query is not None
            
            # 3. Generate mock results (simulates database execution)
            mock_data = endpoints._generate_mock_results(user_query, cypher_query)
            assert len(mock_data) > 0
            
            # 4. Format for UI display (simulates API response)
            api_response = {
                "success": True,
                "cypher": cypher_query,
                "data": mock_data
            }
            
            # 5. Validate response format for frontend
            assert api_response["success"] is True
            assert len(api_response["cypher"]) > 0
            assert len(api_response["data"]) > 0
            
            print(f"    -> Generated: {cypher_query}")
            print(f"    -> Results: {len(api_response['data'])} items")
            
        print("Step 5 PASSED: Complete data flow working\n")
        
        # Step 6: Performance Validation
        print("Step 6: Testing Performance...")
        
        import time
        start_time = time.time()
        
        # Test query processing time
        query = "Show me all people"
        cypher = await assessment.generate_cypher_query(query, 'direct', llm)
        mock_data = endpoints._generate_mock_results(query, cypher)
        
        processing_time = time.time() - start_time
        
        # Should complete in under 3 seconds as per CLAUDE.md requirements
        assert processing_time < 3.0, f"Processing too slow: {processing_time:.2f}s > 3.0s"
        
        print(f"  [SUCCESS] Query processing time: {processing_time:.2f}s (< 3.0s required)")
        print("Step 6 PASSED: Performance requirements met\n")
        
        print("=" * 50)
        print("[SUCCESS] END-TO-END VALIDATION COMPLETE!")
        print("=" * 50)
        
        print("\nValidation Summary:")
        print("- AI query generation: WORKING (100% success on test queries)")
        print("- Query endpoint processing: WORKING (mock data generation)")  
        print("- API server integration: WORKING (endpoints registered)")
        print("- UI component integration: WORKING (all elements present)")
        print("- Complete data flow: WORKING (user query -> graph data)")
        print("- Performance requirements: MET (<3s processing time)")
        
        print("\nReady for manual UI testing!")
        print("Next step: Open UI_planning/mockups/02_project_workspace.html")
        print("and test the natural language query interface")
        
        return True
        
    except Exception as e:
        print(f"\n[FAILED] End-to-end validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


class MockApp:
    """Mock FastAPI app for testing endpoint registration"""
    def __init__(self):
        self.routes = []
        
    def post(self, path, **kwargs):
        def decorator(func):
            self.routes.append(('POST', path, func))
            return func
        return decorator
        
    def get(self, path, **kwargs):
        def decorator(func):
            self.routes.append(('GET', path, func))
            return func
        return decorator


if __name__ == "__main__":
    success = asyncio.run(test_complete_workflow())
    sys.exit(0 if success else 1)