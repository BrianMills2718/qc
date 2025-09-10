#!/bin/bash

echo "=== Qualitative Coding System Startup ==="
echo ""

# 1. Check Docker
echo "Step 1: Checking Docker..."
if ! docker --version > /dev/null 2>&1; then
    echo "ERROR: Docker is not installed or not running"
    echo "Please install Docker Desktop and try again"
    exit 1
fi
echo "✓ Docker is installed"

# 2. Start Neo4j
echo ""
echo "Step 2: Starting Neo4j..."
docker-compose up -d
sleep 5

# 3. Verify Neo4j is running
echo ""
echo "Step 3: Verifying Neo4j connection..."
if curl -s http://localhost:7474 > /dev/null; then
    echo "✓ Neo4j is running on port 7474"
else
    echo "ERROR: Neo4j is not accessible"
    echo "Check docker logs: docker logs qualitative_coding_neo4j_1"
    exit 1
fi

# 4. Check environment
echo ""
echo "Step 4: Checking environment..."
if [ -f .env ]; then
    echo "✓ .env file exists"
    if grep -q "GEMINI_API_KEY" .env; then
        echo "✓ Gemini API key configured"
    else
        echo "WARNING: Gemini API key not found in .env"
    fi
else
    echo "ERROR: .env file not found"
    echo "Copy .env.example to .env and add your API keys"
    exit 1
fi

# 5. Run quick validation
echo ""
echo "Step 5: Running quick validation tests..."
python -m pytest tests/test_fail_fast_validation.py -q

echo ""
echo "=== System Ready ==="
echo ""
echo "To run full test suite:"
echo "  python -m pytest tests/ -v"
echo ""
echo "To analyze an interview:"
echo "  python -m qc.cli analyze sample_interview.txt"
echo ""
echo "To stop Neo4j:"
echo "  docker-compose down"