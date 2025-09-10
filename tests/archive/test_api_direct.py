#!/usr/bin/env python3
"""
Direct API function testing without running the server
"""

import asyncio
import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the specific function we need to test
from web_interface.app import get_entity_network_fixed


async def main():
    """Test the API function directly"""
    print("TESTING get_entity_network_fixed FUNCTION DIRECTLY")
    print("=" * 55)
    
    try:
        # Call the function directly
        result = await get_entity_network_fixed("AI")
        
        print("API function executed successfully")
        print(f"Result type: {type(result)}")
        
        # Check the structure
        if isinstance(result, dict):
            print(f"Entity name: {result.get('entity_name', 'N/A')}")
            
            network = result.get('network', {})
            print(f"Network keys: {list(network.keys())}")
            
            # Check for entity_relationships field
            if 'entity_relationships' in network:
                relationships = network['entity_relationships']
                print(f"PASS: entity_relationships field present")
                print(f"Relationships count: {len(relationships)}")
                print(f"Relationships type: {type(relationships)}")
                
                if relationships:
                    print("Sample relationships:")
                    for rel in relationships[:3]:
                        print(f"  {rel}")
                else:
                    print("WARNING: entity_relationships is empty array")
            else:
                print("FAIL: entity_relationships field MISSING from network")
            
            # Print full network structure for debugging
            print(f"\nFull network structure:")
            for key, value in network.items():
                if isinstance(value, list):
                    print(f"  {key}: list with {len(value)} items")
                else:
                    print(f"  {key}: {type(value).__name__} = {value}")
            
        else:
            print(f"ERROR: Result is not a dict: {result}")
        
        return result
        
    except Exception as e:
        print(f"ERROR: API function failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(main())
    
    if result:
        print("\n" + "=" * 55)
        print("SUCCESS: API function call completed")
        network = result.get('network', {})
        if 'entity_relationships' in network and network['entity_relationships']:
            print("PASS: Backend API is working correctly")
        else:
            print("FAIL: Backend API not returning relationships correctly")
    else:
        print("FAIL: API function call failed")