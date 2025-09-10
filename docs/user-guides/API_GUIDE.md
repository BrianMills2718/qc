# REST API Guide

Complete guide for using the Qualitative Coding Analysis REST API.

## Quick Start

### Start the API Server

```bash
# Using CLI command
python -m qc.cli serve --host 0.0.0.0 --port 8000

# Or using the dedicated script
python run_api_server.py

# For development with auto-reload
python -m qc.cli serve --reload
```

### Access API Documentation

- **Interactive API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Core Endpoints

### 1. Root Information
```http
GET /
```

Returns basic API information and available endpoints.

**Response:**
```json
{
  "message": "Qualitative Coding Analysis API",
  "version": "1.0.0",
  "endpoints": {
    "analyze": "/analyze",
    "status": "/jobs/{job_id}",
    "query": "/query",
    "health": "/health",
    "docs": "/docs"
  }
}
```

### 2. Interview Analysis
```http
POST /analyze
```

Submit interview text for analysis and entity extraction.

**Request Body:**
```json
{
  "text": "Your interview text here...",
  "validation_mode": "hybrid",
  "session_id": "optional-session-id",
  "metadata": {
    "participant_id": "P001",
    "interview_date": "2025-01-15"
  }
}
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "session_id": "session-id-if-provided",
  "entities_found": 0,
  "relationships_found": 0,
  "codes_found": 0
}
```

**Validation Modes:**
- `hybrid`: Balanced extraction (default)
- `academic`: Academic research standards
- `exploratory`: Maximum discovery flexibility

### 3. Job Status Tracking
```http
GET /jobs/{job_id}
```

Check the status and results of an analysis job.

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "created_at": "2025-01-15T10:30:00Z",
  "completed_at": "2025-01-15T10:32:15Z",
  "progress": 1.0,
  "results": {
    "entities_found": 25,
    "relationships_found": 18,
    "codes_found": 12,
    "extraction_results": {
      "entities": [...],
      "relationships": [...],
      "codes": [...]
    }
  }
}
```

**Status Values:**
- `queued`: Job waiting to start
- `processing`: Analysis in progress
- `completed`: Analysis finished successfully
- `failed`: Analysis encountered an error
- `cancelled`: Job was cancelled

### 4. Job Management
```http
GET /jobs?status_filter=completed&limit=10
DELETE /jobs/{job_id}
```

List jobs with optional filtering and cancel running jobs.

### 5. Natural Language Queries
```http
POST /query
```

Query extracted data using natural language.

**Request Body:**
```json
{
  "query": "What do senior people say about AI?",
  "session_id": "optional-session-filter", 
  "limit": 10
}
```

### 6. Health Monitoring
```http
GET /health
```

Comprehensive system health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "uptime_seconds": 3600,
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 45.2
    },
    "llm": {
      "status": "healthy",
      "response_time_ms": 1250.8
    },
    "memory": {
      "status": "healthy"
    }
  }
}
```

**HTTP Status Codes:**
- `200`: System healthy
- `206`: System degraded but functional
- `503`: System unhealthy

## Integration Examples

### Python with Requests

```python
import requests
import time

# Start analysis
response = requests.post('http://localhost:8000/analyze', json={
    'text': 'Your interview text here...',
    'validation_mode': 'hybrid'
})
job_id = response.json()['job_id']

# Poll for completion
while True:
    status_response = requests.get(f'http://localhost:8000/jobs/{job_id}')
    job_status = status_response.json()
    
    if job_status['status'] == 'completed':
        results = job_status['results']
        print(f"Found {results['entities_found']} entities")
        break
    elif job_status['status'] == 'failed':
        print(f"Analysis failed: {job_status.get('error_message')}")
        break
    
    time.sleep(5)  # Wait 5 seconds before checking again
```

### JavaScript with Fetch

```javascript
// Start analysis
const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Your interview text here...',
    validation_mode: 'hybrid'
  })
});
const { job_id } = await response.json();

// Poll for completion
async function waitForCompletion(jobId) {
  while (true) {
    const statusResponse = await fetch(`http://localhost:8000/jobs/${jobId}`);
    const jobStatus = await statusResponse.json();
    
    if (jobStatus.status === 'completed') {
      console.log(`Found ${jobStatus.results.entities_found} entities`);
      return jobStatus.results;
    } else if (jobStatus.status === 'failed') {
      throw new Error(`Analysis failed: ${jobStatus.error_message}`);
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
  }
}

const results = await waitForCompletion(job_id);
```

### cURL Examples

```bash
# Start analysis
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your interview text here...",
    "validation_mode": "hybrid"
  }'

# Check job status
curl "http://localhost:8000/jobs/{job-id}"

# Query data
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What themes emerge about technology?"}'

# Health check
curl "http://localhost:8000/health"
```

## Configuration

### Environment Variables

- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)
- `API_WORKERS`: Number of workers (default: 1)
- `API_RELOAD`: Enable auto-reload (default: false)
- `LOG_LEVEL`: Logging level (default: info)

### CORS Configuration

The API includes CORS middleware for web integration. For production, configure `allow_origins` to specific domains:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

## Error Handling

### Common HTTP Status Codes

- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found (job/resource doesn't exist)
- `422`: Validation Error (invalid request format)
- `500`: Internal Server Error
- `503`: Service Unavailable (health check failed)

### Error Response Format

```json
{
  "detail": "Error description",
  "status_code": 400,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Performance Considerations

### Concurrent Analysis

- Default: 1 worker, handles requests sequentially
- Production: Increase workers for concurrent processing
- Background jobs: Analysis runs asynchronously

### Rate Limiting

Consider implementing rate limiting for production:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/analyze")
@limiter.limit("5/minute")
async def analyze_interview(request: Request, ...):
    # Analysis logic
```

### Caching

For improved performance, consider caching:
- Health check results (30 seconds)
- Query results (based on query hash)
- LLM responses (if acceptable for use case)

## Monitoring and Logging

### Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/api.log'),
        logging.StreamHandler()
    ]
)
```

### Health Monitoring

Regular health checks monitor:
- Database connectivity and performance
- LLM service availability and response time
- System memory usage
- Overall system status

### Metrics Collection

Consider implementing metrics collection:
- Request count and response times
- Analysis job success/failure rates
- Resource utilization
- Error rates by endpoint

## Deployment

### Docker Deployment

See `DEPLOYMENT.md` for complete Docker deployment instructions.

### Production Checklist

- [ ] Configure environment variables
- [ ] Set up proper CORS origins
- [ ] Implement rate limiting
- [ ] Configure logging to files
- [ ] Set up health monitoring
- [ ] Configure reverse proxy (nginx/Apache)
- [ ] Set up SSL/TLS certificates
- [ ] Configure database persistence
- [ ] Set up backup procedures

## Troubleshooting

### Common Issues

1. **Analysis Jobs Fail**
   - Check Neo4j connectivity
   - Verify Gemini API key
   - Check input text format

2. **Health Check Returns 503**
   - Check database connection
   - Verify LLM client configuration
   - Check system resources

3. **High Response Times**
   - Monitor system resources
   - Check database performance
   - Consider increasing workers

### Debug Mode

Start the server with reload for debugging:

```bash
python -m qc.cli serve --reload --host 127.0.0.1 --port 8000
```

This enables:
- Auto-reload on code changes
- Detailed error messages
- Enhanced logging