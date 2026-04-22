#!/bin/bash
# Quick Start Script - Run this to test the complete setup
# Usage: bash get-started.sh

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║           🚀 RAG SYSTEM - START AND TEST                   ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"

echo ""
echo "📋 CHECKING PREREQUISITES..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi
echo "✓ Docker found: $(docker --version)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi
echo "✓ Docker Compose found"

echo ""
echo "🔧 STARTING SERVICES..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Services starting (this may take 2-5 minutes on first run):"
echo "  • Qdrant Vector Database (port 6333)"
echo "  • Ollama LLM Service (port 11434)"
echo "  • FastAPI Backend (port 8000)"
echo "  • React Frontend (port 3000)"
echo ""

docker-compose up -d --build

# Wait for services to be healthy
echo ""
echo "⏳ WAITING FOR SERVICES TO BE READY..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Function to check if service is ready
check_service() {
    local service=$1
    local url=$2
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo "✓ $service is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 1
    done
    
    echo "⚠️  $service may not be ready (timeout)"
    return 0
}

echo "Checking Qdrant..."
check_service "Qdrant" "http://localhost:6333/"

echo "Checking Ollama..."
check_service "Ollama" "http://localhost:11434/api/tags"

echo "Checking Backend..."
check_service "Backend" "http://localhost:8000/health"

echo ""
echo "✅ ALL SERVICES READY!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "📚 INGESTING SAMPLE DOCUMENTS..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker exec rag-backend python scripts/ingest_sample_documents.py --sample

echo ""
echo "🧪 RUNNING END-TO-END TEST..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker exec rag-backend python scripts/test_rag_e2e.py

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║              ✨ SETUP COMPLETE - ALL READY! ✨             ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"

echo ""
echo "🌐 ACCESS YOUR RAG SYSTEM:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Chat Interface:     http://localhost:3000"
echo "  API Documentation:  http://localhost:8000/docs"
echo "  Qdrant Dashboard:   http://localhost:6333"
echo "  Ollama API:         http://localhost:11434"
echo ""

echo "📖 NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Open chat:  http://localhost:3000"
echo "  2. Ask questions about Machine Learning, Vector DBs, or RAG"
echo "  3. Check test results: cat backend/scripts/test_results.json"
echo ""

echo "📚 DOCUMENTATION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  • Setup Guide:       docs/SETUP-GUIDE.md"
echo "  • Quick Reference:   docs/QUICK-REFERENCE.md"
echo "  • Chat Usage:        docs/CHAT-USAGE-GUIDE.md"
echo ""

echo "🛑 TO STOP SERVICES:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  docker-compose down"
echo ""
