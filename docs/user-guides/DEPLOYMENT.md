# Production Deployment Guide

This guide covers deploying the Qualitative Coding Analysis Tool to production environments.

## Prerequisites

- Docker and Docker Compose installed
- Valid Gemini API key
- At least 4GB RAM recommended
- 10GB disk space for data storage

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd qualitative_coding
   ```

2. **Configure Environment**
   ```bash
   cp .env.production.template .env.production
   # Edit .env.production with your settings
   ```

3. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.production.yml up -d
   ```

4. **Verify Deployment**
   ```bash
   # Check service health
   curl http://localhost:8000/health
   
   # Check Neo4j Browser
   open http://localhost:7474
   ```

## Configuration

### Required Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key
- `NEO4J_PASSWORD`: Secure password for Neo4j database
- `SECRET_KEY`: 32+ character secret key for application security

### Optional Configuration

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MAX_CONCURRENT_REQUESTS`: Maximum concurrent analysis requests
- `DATABASE_POOL_SIZE`: Neo4j connection pool size

## Security Best Practices

### 1. API Key Management
- Never commit API keys to version control
- Use environment variables or secrets management
- Rotate API keys regularly

### 2. Database Security
- Use strong passwords (16+ characters)
- Enable Neo4j authentication
- Consider network isolation

### 3. Network Security
- Use HTTPS in production
- Configure firewall rules
- Consider reverse proxy (nginx/Apache)

### 4. Container Security
- Application runs as non-root user
- Minimal base image (python:3.11-slim)
- Regular security updates

## Monitoring

### Health Checks

The application provides comprehensive health monitoring:

```bash
# System health endpoint
curl http://localhost:8000/health

# Component-specific checks
curl http://localhost:8000/health/database
curl http://localhost:8000/health/llm
```

### Health Check Response Format

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
      "status": "healthy",
      "error_message": null
    }
  }
}
```

### Status Levels

- **healthy**: All systems operating normally
- **degraded**: Some performance issues but functional
- **unhealthy**: Critical issues requiring attention

## Scaling

### Horizontal Scaling

To run multiple application instances:

```yaml
services:
  qualitative-coding:
    # ... existing config
    deploy:
      replicas: 3
    # Add load balancer configuration
```

### Database Scaling

For high-throughput scenarios:

1. Increase Neo4j memory allocation
2. Add read replicas
3. Optimize Cypher queries
4. Consider clustering for enterprise use

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker exec neo4j neo4j-admin database dump neo4j backup.dump

# Restore backup
docker exec neo4j neo4j-admin database load neo4j backup.dump
```

### Application Data

- Analysis results stored in Neo4j (backed up above)
- Configuration files in version control
- Logs in Docker volumes (configure retention)

## Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   ```bash
   # Check Neo4j logs
   docker logs <neo4j-container-id>
   
   # Verify credentials
   docker exec -it <neo4j-container> cypher-shell -u neo4j -p <password>
   ```

2. **Gemini API Errors**
   ```bash
   # Test API key
   curl -H "Authorization: Bearer $GEMINI_API_KEY" \
        https://generativelanguage.googleapis.com/v1/models
   ```

3. **Memory Issues**
   ```bash
   # Check memory usage
   docker stats
   
   # Increase container memory limits
   # Edit docker-compose.production.yml
   ```

### Log Analysis

```bash
# Application logs
docker logs qualitative-coding-app

# Database logs
docker logs qualitative-coding-neo4j

# Follow logs in real-time
docker logs -f qualitative-coding-app
```

## Performance Optimization

### Database Performance

1. **Memory Tuning**
   ```env
   NEO4J_dbms_memory_heap_initial_size=1G
   NEO4J_dbms_memory_heap_max_size=4G
   NEO4J_dbms_memory_pagecache_size=2G
   ```

2. **Index Optimization**
   - Indexes created automatically
   - Monitor query performance
   - Add custom indexes if needed

### Application Performance

1. **Concurrency Settings**
   ```env
   MAX_CONCURRENT_REQUESTS=20
   DATABASE_POOL_SIZE=15
   ```

2. **Caching**
   - LLM response caching (future enhancement)
   - Query result caching
   - Static asset caching

## Updates and Maintenance

### Application Updates

```bash
# Pull latest images
docker-compose -f docker-compose.production.yml pull

# Restart services
docker-compose -f docker-compose.production.yml up -d

# Clean up old images
docker image prune
```

### Database Maintenance

```bash
# Database statistics
docker exec neo4j cypher-shell -u neo4j -p <password> \
  "CALL db.stats.retrieve('GRAPH COUNTS')"

# Clean up unused data
docker exec neo4j cypher-shell -u neo4j -p <password> \
  "CALL apoc.periodic.iterate('MATCH (n) WHERE NOT (n)--() RETURN n', 'DELETE n', {batchSize:1000})"
```

## Support

For production support:
1. Check application logs
2. Verify system health endpoints
3. Review resource utilization
4. Consult troubleshooting section above

For critical issues, ensure you have:
- Current system health status
- Relevant log excerpts
- Environment configuration (without secrets)
- Steps to reproduce the issue