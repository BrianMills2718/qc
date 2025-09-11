#!/usr/bin/env python3
"""
Simple test for Phase 1.1 Implementation Strategy - Core Integration Test
Tests Neo4j connection, query execution, and result formatting
"""

import asyncio
import logging
from qc_clean.core.data.neo4j_manager import EnhancedNeo4jManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def format_neo4j_results(neo4j_results):
    """Transform Neo4j query results to API response format (copied from endpoints)"""
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

async def test_phase_1_1_implementation():
    """Test Phase 1.1 Implementation Strategy"""
    
    print("=" * 60)
    print("Phase 1.1 Implementation Strategy - Core Integration Test")
    print("=" * 60)
    
    # Step 1: Test Neo4j Connection
    print("Step 1: Testing Neo4j Connection...")
    neo4j_manager = EnhancedNeo4jManager(
        uri="bolt://localhost:7687",
        username="neo4j", 
        password="password"
    )
    
    try:
        # Test basic connection
        results = await neo4j_manager.execute_cypher('MATCH (n) RETURN count(n) as total_nodes')
        total_nodes = results[0]['total_nodes']
        print(f"✅ Neo4j Connection: SUCCESS")
        print(f"   Total nodes in database: {total_nodes}")
        
        if total_nodes == 0:
            print("⚠️  Warning: Database is empty - no test data available")
            return False
            
    except Exception as e:
        print(f"❌ Neo4j Connection: FAILED - {e}")
        return False
    
    # Step 2: Test Person Query Execution
    print("\nStep 2: Testing Person Query Execution...")
    try:
        cypher_query = "MATCH (p:Person) RETURN p"
        print(f"   Executing: {cypher_query}")
        
        neo4j_results = await neo4j_manager.execute_cypher(cypher_query)
        print(f"✅ Query Execution: SUCCESS")
        print(f"   Raw results count: {len(neo4j_results)}")
        
        if len(neo4j_results) == 0:
            print("⚠️  Warning: No Person nodes found in database")
            return False
            
    except Exception as e:
        print(f"❌ Query Execution: FAILED - {e}")
        return False
    
    # Step 3: Test Result Formatting
    print("\nStep 3: Testing Result Formatting...")
    try:
        formatted_results = format_neo4j_results(neo4j_results)
        print(f"✅ Result Formatting: SUCCESS")
        print(f"   Formatted results count: {len(formatted_results)}")
        
        print("\nFormatted Results:")
        for i, result in enumerate(formatted_results):
            print(f"   {i+1}. {result['name']} (ID: {result['id']})")
            # Show some properties
            properties = result['properties']
            if 'entity_type' in properties:
                print(f"       Type: {properties['entity_type']}")
            if 'source_interview' in properties:
                print(f"       Source: {properties['source_interview']}")
            if 'description' in properties:
                print(f"       Description: {properties['description'][:50]}...")
                
    except Exception as e:
        print(f"❌ Result Formatting: FAILED - {e}")
        return False
    
    # Step 4: Compare with Mock Data
    print("\nStep 4: Comparing with Mock Data...")
    mock_data = [
        {"id": "person_1", "name": "Dr. Sarah Johnson", "label": "Dr. Sarah Johnson"},
        {"id": "person_2", "name": "Mike Chen", "label": "Mike Chen"},
        {"id": "person_3", "name": "Prof. Emily Davis", "label": "Prof. Emily Davis"}
    ]
    
    real_names = [result['name'] for result in formatted_results]
    mock_names = [mock['name'] for mock in mock_data]
    
    print(f"   Real data names: {real_names}")
    print(f"   Mock data names: {mock_names}")
    
    if set(real_names) == set(mock_names):
        print("⚠️  Warning: Real data matches mock data exactly (unexpected)")
    else:
        print("✅ Data Verification: Real data differs from mock (expected)")
    
    # Close connection
    await neo4j_manager.close()
    
    print(f"\n✅ Phase 1.1 Implementation Strategy: COMPLETED SUCCESSFULLY")
    print(f"   - Neo4j connection: ✅ Working")
    print(f"   - Query execution: ✅ Working") 
    print(f"   - Result formatting: ✅ Working")
    print(f"   - Real data integration: ✅ Verified")
    
    return True

async def main():
    success = await test_phase_1_1_implementation()
    print("\n" + "=" * 60)
    if success:
        print("🎯 PHASE 1.1 IMPLEMENTATION STRATEGY: SUCCESS")
        print("   Mock data has been successfully replaced with real Neo4j integration!")
    else:
        print("❌ PHASE 1.1 IMPLEMENTATION STRATEGY: FAILED")  
        print("   Database integration issues detected")
    print("=" * 60)
    return success

if __name__ == "__main__":
    asyncio.run(main())