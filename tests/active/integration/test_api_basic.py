#!/usr/bin/env python3
"""
Basic API functionality test
"""
import asyncio
import json
from src.qc.api.main import app
from fastapi.testclient import TestClient

def test_api_endpoints():
    """Test basic API endpoints"""
    client = TestClient(app)
    
    print("Testing API endpoints...")
    
    # Test root endpoint
    response = client.get("/")
    print(f"Root endpoint: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    
    # Test health endpoint
    response = client.get("/health")
    print(f"Health endpoint: {response.status_code}")
    
    # Test OpenAPI docs
    response = client.get("/docs")
    print(f"API docs: {response.status_code}")
    
    print("Basic API tests completed!")

if __name__ == "__main__":
    test_api_endpoints()