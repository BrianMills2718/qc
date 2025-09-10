#!/usr/bin/env python3
"""
Test Web Interface - Verify Entity Relationships via API

Test that the entity extraction system is working through the API.
"""

import requests
import json

def test_web_interface():
    """Test the web interface API endpoints"""
    
    base_url = "http://localhost:8000"
    
    print("=== TESTING WEB INTERFACE API ===")
    
    # Test health endpoint
    try:
        health_response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health Check: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"Database Status: {health_data.get('neo4j_status', 'Unknown')}")
        
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Look for stats or summary endpoint
    endpoints_to_try = [
        "/stats",
        "/summary", 
        "/database/stats",
        "/entities",
        "/quotes",
        "/codes"
    ]
    
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"SUCCESS {endpoint}:")
                print(json.dumps(data, indent=2)[:500] + "...")
                break
            else:
                print(f"{endpoint}: {response.status_code}")
                
        except Exception as e:
            print(f"{endpoint}: Failed - {e}")
    
    print(f"\n🌐 API Documentation: {base_url}/docs")
    print(f"📊 Alternative Docs: {base_url}/redoc")

if __name__ == "__main__":
    test_web_interface()