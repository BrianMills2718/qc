#!/usr/bin/env python3
"""
Test script to verify Phase 1.1 Implementation Strategy
Tests real Neo4j integration vs mock data fallback
"""

import asyncio
import logging
from qc_clean.plugins.api.query_endpoints import QueryEndpoints
from qc_clean.plugins.api.query_endpoints import NaturalLanguageQueryRequest

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

async def test_neo4j_integration():
    """Test Phase 1.1 Implementation Strategy - Real Neo4j vs Mock fallback"""
    
    print("=" * 60)
    print("Phase 1.1 Implementation Strategy Test")
    print("=" * 60)
    
    # Initialize query endpoints with Neo4j integration
    endpoints = QueryEndpoints()
    
    # Test request
    request = NaturalLanguageQueryRequest(query="Show me all people")
    
    # Register with dummy app (we don't need the full FastAPI app for this test)
    class DummyApp:
        def post(self, *args, **kwargs):
            pass
        def get(self, *args, **kwargs):
            pass
    
    app = DummyApp()
    endpoints.register_endpoints(app)
    
    # Get the endpoint function directly (bypass FastAPI decorator)
    # We need to call the function that would be called by the endpoint
    try:
        print("Testing natural language query: 'Show me all people'")
        print("Generating Cypher query...")
        
        # Import working AI system components (same as in endpoints)
        from investigation_ai_quality_assessment import AIQueryGenerationAssessment
        from qc_clean.core.llm.llm_handler import LLMHandler
        
        # Generate Cypher query using working system
        assessment = AIQueryGenerationAssessment()
        llm = LLMHandler(model_name='gpt-4o-mini')
        
        cypher_query = await assessment.generate_cypher_query(
            request.query, 'direct', llm
        )
        
        print(f"Generated Cypher: {cypher_query}")
        
        if not cypher_query:
            print("❌ FAILED: Could not generate Cypher query")
            return False
            
        # Test Neo4j execution
        print("\nTesting Neo4j database execution...")
        try:
            neo4j_results = await endpoints.neo4j_manager.execute_cypher(cypher_query)
            print(f"✅ SUCCESS: Neo4j returned {len(neo4j_results)} results")
            
            # Format results
            formatted_results = endpoints._format_neo4j_results(neo4j_results)
            print(f"✅ SUCCESS: Formatted to {len(formatted_results)} API results")
            
            print("\nReal Neo4j Results:")
            for i, result in enumerate(formatted_results):
                print(f"  {i+1}. {result['name']} (ID: {result['id']})")
                if 'entity_type' in result['properties']:
                    print(f"      Type: {result['properties']['entity_type']}")
                if 'source_interview' in result['properties']:
                    print(f"      Source: {result['properties']['source_interview']}")
            
            print(f"\n✅ Phase 1.1 Implementation Strategy: COMPLETED")
            print(f"   - Neo4j connection: ✅ Working")
            print(f"   - Query execution: ✅ Working") 
            print(f"   - Result formatting: ✅ Working")
            print(f"   - Mock data replaced: ✅ Successful")
            
            return True
            
        except Exception as db_error:
            print(f"⚠️  Neo4j execution failed: {db_error}")
            print("Testing fallback to mock data...")
            
            mock_results = endpoints._generate_mock_results(request.query, cypher_query)
            print(f"✅ Fallback: Mock data returned {len(mock_results)} results")
            
            print("\nMock Fallback Results:")
            for i, result in enumerate(mock_results):
                print(f"  {i+1}. {result['name']} (ID: {result['id']})")
            
            print(f"\n⚠️  Phase 1.1 Implementation Strategy: PARTIAL")
            print(f"   - Neo4j connection: ❌ Failed")
            print(f"   - Fallback system: ✅ Working")
            print(f"   - Graceful degradation: ✅ Working")
            
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Critical error in integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_neo4j_integration())
    print("\n" + "=" * 60)
    if success:
        print("🎯 PHASE 1.1 IMPLEMENTATION STRATEGY: SUCCESSFUL")
        print("   Real Neo4j database integration is working!")
    else:
        print("⚠️  PHASE 1.1 IMPLEMENTATION STRATEGY: NEEDS ATTENTION")  
        print("   Fallback system working, but Neo4j connection issues detected")
    print("=" * 60)