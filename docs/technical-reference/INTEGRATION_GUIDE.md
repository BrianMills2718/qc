# Integration Guide for Parallel Development

## Overview
This guide explains how to integrate the three parallel tracks into a working system.

## Quick Start

### 1. Start All Three Tracks Independently

**Terminal 1 - Backend Core (Track 1)**
```bash
cd track1_backend
# Develop analyzer.py independently
# Test with real interviews from tests/fixtures/
python src/analyzer.py
```

**Terminal 2 - API Server (Track 2)**
```bash
cd track2_api
# Run API with stub analyzer initially
pip install fastapi uvicorn python-multipart
uvicorn src.api:app --reload
```

**Terminal 3 - Frontend (Track 3)**
```bash
cd track3_frontend
# Run React app with mock API initially
npm install
npm start
```

## Integration Points

### Day 1-3: Independent Development
Each track works independently using stubs/mocks:

1. **Track 1** develops analyzer using test interviews
2. **Track 2** develops API using stub analyzer
3. **Track 3** develops UI using mock API

### Day 4: Integration

#### Step 1: Connect Track 1 → Track 2
Once Track 1's analyzer works:
```python
# In track2_api/src/api.py, the import will automatically work:
from analyzer import QualitativeAnalyzer  # Real analyzer replaces stub
```

#### Step 2: Connect Track 2 → Track 3
Once Track 2's API works:
```javascript
// In track3_frontend/src/api.js, switch from mock to real:
const API_URL = 'http://localhost:8000';  // Real API
// const API_URL = null;  // Comment out to use mock
```

#### Step 3: Test Full Flow
```bash
# 1. Upload test interview
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "Integration Test"}'

# 2. Upload file
curl -X POST http://localhost:8000/api/sessions/{id}/interviews \
  -F "files=@tests/fixtures/interviews/trust_remote_work.txt"

# 3. Start analysis
curl -X POST http://localhost:8000/api/sessions/{id}/analyze

# 4. Check results
curl http://localhost:8000/api/sessions/{id}/codes
```

## Common Integration Issues

### Issue: "Module not found: analyzer"
**Solution**: Ensure Track 1 is in the Python path:
```python
# In track2_api/src/api.py
import sys
sys.path.append('../../track1_backend/src')
```

### Issue: CORS errors in browser
**Solution**: Track 2 API already includes CORS middleware for localhost:3000

### Issue: API connection refused
**Solution**: Ensure Track 2 API is running on port 8000

## Testing Integration

### Integration Test Script
```python
# tests/test_integration.py
import requests
import time

def test_full_workflow():
    # 1. Create session
    session = requests.post("http://localhost:8000/api/sessions", 
                          json={"name": "Test"}).json()
    session_id = session['id']
    
    # 2. Upload interview
    with open("fixtures/interviews/trust_remote_work.txt", 'rb') as f:
        files = {'files': ('interview.txt', f, 'text/plain')}
        requests.post(f"http://localhost:8000/api/sessions/{session_id}/interviews", 
                     files=files)
    
    # 3. Start analysis
    task = requests.post(f"http://localhost:8000/api/sessions/{session_id}/analyze").json()
    task_id = task['task_id']
    
    # 4. Wait for completion
    while True:
        status = requests.get(f"http://localhost:8000/api/tasks/{task_id}/status").json()
        if status['status'] == 'completed':
            break
        time.sleep(1)
    
    # 5. Check results
    codes = requests.get(f"http://localhost:8000/api/sessions/{session_id}/codes").json()
    
    # Verify we found expected codes
    code_names = [c['name'] for c in codes]
    assert 'trust_issues' in ' '.join(code_names).lower()
    print(f"✓ Found {len(codes)} codes")
    
if __name__ == "__main__":
    test_full_workflow()
```

## Parallel Development Benefits

1. **3x Faster**: All tracks develop simultaneously
2. **No Blocking**: Track 3 can build UI while Track 1 develops analyzer
3. **Early Testing**: Each track can test independently
4. **Clear Contracts**: Shared contracts ensure compatibility

## Final Integration Checklist

- [ ] Track 1: Analyzer extracts codes from real interviews
- [ ] Track 2: API endpoints all return correct status codes
- [ ] Track 3: UI can upload files and display results
- [ ] Integration: Full workflow works end-to-end
- [ ] Export: CSV download works correctly

## Next Steps

After integration:
1. Deploy with Docker Compose
2. Add error handling for edge cases
3. Optimize performance
4. Add more interview fixtures for testing