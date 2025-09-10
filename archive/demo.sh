#!/bin/bash
# One-Click Demo Launcher for Unix/Linux/Mac
# Launch the qualitative coding analysis tool with pre-loaded AI research data

set -e

echo "🚀 Qualitative Coding Analysis Tool - One-Click Demo"
echo "=================================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "💡 Please install Python 3.8+ and try again"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "src/qc" ]; then
    echo "❌ Please run this script from the qualitative-coding root directory"
    echo "💡 Expected structure: src/qc/, requirements.txt, etc."
    exit 1
fi

echo "✅ Environment check passed"
echo ""

# Ask user preference
echo "Choose demo launch method:"
echo "1) Docker (recommended - isolated environment)"
echo "2) Local Python (direct installation)"
echo "3) Quick Docker Hub pull (fastest)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "🐳 Launching with Docker..."
        if ! command -v docker-compose &> /dev/null; then
            echo "❌ Docker Compose is required but not installed"
            echo "💡 Please install Docker and Docker Compose"
            exit 1
        fi
        
        docker-compose -f config/docker/docker-compose.demo.yml up --build
        ;;
    2)
        echo "🐍 Launching with local Python..."
        python3 scripts/launch_demo.py
        ;;
    3)
        echo "⚡ Quick Docker Hub launch..."
        echo "🚧 Docker Hub image coming soon - using local Docker for now"
        docker-compose -f config/docker/docker-compose.demo.yml up --build
        ;;
    *)
        echo "❌ Invalid choice. Please run again and choose 1, 2, or 3."
        exit 1
        ;;
esac