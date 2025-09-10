#!/usr/bin/env python3
"""
Test the live API server endpoint
"""

import requests
import json
import time

def test_api_endpoint():
    """Test the API endpoint with server running"""
    print("TESTING LIVE API ENDPOINT")
    print("=" * 30)
    
    # Test the API endpoint
    url = "http://127.0.0.1:8000/api/entity/AI/network"
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("API Response received successfully")
            
            # Check structure
            if 'network' in data:
                network = data['network']
                print(f"Network keys: {list(network.keys())}")
                
                if 'entity_relationships' in network:
                    relationships = network['entity_relationships']
                    print(f"PASS: entity_relationships field present")
                    print(f"Relationships count: {len(relationships)}")
                    
                    if relationships:
                        print("Sample relationships:")
                        for rel in relationships[:3]:
                            print(f"  {rel}")
                        return True
                    else:
                        print("WARNING: entity_relationships is empty")
                        return False
                else:
                    print("FAIL: entity_relationships field missing")
                    return False
            else:
                print("FAIL: No network field in response")
                return False
        else:
            print(f"ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server")
        print("Make sure the server is running on port 8000")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("Waiting 3 seconds for server to be ready...")
    time.sleep(3)
    
    success = test_api_endpoint()
    
    if success:
        print("\nSUCCESS: API endpoint working correctly!")
    else:
        print("\nFAIL: API endpoint not working correctly")
    
    return success

if __name__ == "__main__":
    main()