#!/bin/bash
# Docker & RAG Framework Setup Script
# Run this script to set up Docker and start the RAG application

set -e

echo "🔧 RAG Framework Docker Setup"
echo "=============================="

# Step 1: Check Docker installation
echo -e "\n📦 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first:"
    echo "   Linux: https://docs.docker.com/engine/install/"
    echo "   macOS/Windows: https://www.docker.com/products/docker-desktop"
    exit 1
fi

DOCKER_VERSION=$(docker --version)
echo "✓ Docker installed: $DOCKER_VERSION"

# Step 2: Check Docker daemon
echo -e "\n🚀 Checking Docker daemon..."
if ! docker ps &> /dev/null; then
    echo "⚠️  Docker daemon not accessible. Attempting fixes..."
    
    # Try to fix socket permissions
    if [ -S /var/run/docker.sock ]; then
        echo "   Found Docker socket at /var/run/docker.sock"
        echo "   Attempting to fix permissions..."
        sudo chmod 666 /var/run/docker.sock 2>/dev/null && echo "✓ Socket permissions fixed" || echo "⚠️  Could not modify socket (may need manual setup)"
    fi
    
    # Try alternative: add user to docker group
    if ! id -nG | grep -qw docker; then
        echo "   Adding user to docker group..."
        sudo usermod -aG docker $USER 2>/dev/null && echo "✓ User added to docker group" || echo "⚠️  Could not add to docker group"
        echo "   ⚠️  Please log out and back in for group changes to take effect"
    fi
fi

# Step 3: Verify docker-compose
echo -e "\n📦 Checking docker-compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Installing..."
    sudo apt-get update && sudo apt-get install -y docker-compose || \
    echo "❌ Failed to install docker-compose. Please install manually."
    exit 1
fi

COMPOSE_VERSION=$(docker-compose --version)
echo "✓ docker-compose installed: $COMPOSE_VERSION"

# Step 4: Configure API keys
echo -e "\n🔑 API Keys Configuration"
echo "=========================="
ENV_FILE="backend/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  $ENV_FILE not found"
    exit 1
fi

echo "Edit the following keys in $ENV_FILE:"
echo ""
echo "Required keys:"
echo "  • LITELLM_GROQ_API_KEY (from https://console.groq.com/keys)"
echo "  • LITELLM_MISTRAL_API_KEY (from https://console.mistral.ai/api-keys/)"
echo ""
echo "Optional:"
echo "  • QDRANT_ADMIN_KEY (Qdrant authentication)"
echo "  • Azure Storage credentials (for production)"
echo ""
read -p "Press Enter after configuring API keys in $ENV_FILE..."

# Step 5: Build and start services
echo -e "\n🏗️  Building Docker images..."
if docker-compose build 2>&1 | tail -50; then
    echo "✓ Docker images built successfully"
else
    echo "❌ Docker build failed. Check logs above."
    exit 1
fi

echo -e "\n🚀 Starting services..."
echo "Access points:"
echo "  • Backend API: http://localhost:8000"
echo "  • API Docs (Swagger): http://localhost:8000/docs"
echo "  • Frontend: http://localhost:3000"
echo "  • Qdrant: http://localhost:6333"
echo ""

if docker-compose up 2>&1; then
    echo "✓ All services running!"
else
    echo "⚠️  Service startup error. Check logs with: docker-compose logs -f"
fi
