#!/bin/bash
# Migration Verification Script
# Run this after completing the migration to verify everything works

echo "=== MIGRATION VERIFICATION ==="
echo ""

# Check current location
echo "Current working directory: $(pwd)"
echo "Expected: /mnt/d/projects/rag"
echo ""

# Check disk usage
echo "=== DISK USAGE ==="
df -h | grep -E "(Filesystem|C:\|D:\|/dev/sdc|/mnt/[cd])"
echo ""

# Check Docker
echo "=== DOCKER STATUS ==="
if docker --version >/dev/null 2>&1; then
    echo "✅ Docker is installed"
    if docker ps >/dev/null 2>&1; then
        echo "✅ Docker daemon is running"
        echo "Docker data root:"
        docker system info | grep "Docker Root Dir" || echo "  (Not accessible - may be normal for snap Docker)"
    else
        echo "❌ Docker daemon not accessible"
    fi
else
    echo "❌ Docker not found"
fi
echo ""

# Check project files
echo "=== PROJECT FILES ==="
if [ -d "/mnt/d/projects/rag" ]; then
    echo "✅ Project exists on D drive"
    ls -la /mnt/d/projects/rag/ | head -10
else
    echo "❌ Project not found on D drive"
fi
echo ""

# Check secrets
echo "=== SECRETS ==="
if [ -d "/mnt/d/projects/rag/secrets" ]; then
    echo "✅ Secrets directory exists"
    ls -la /mnt/d/projects/rag/secrets/
else
    echo "❌ Secrets directory not found"
fi
echo ""

# Check symlinks
echo "=== SYMLINKS ==="
if [ -L "$HOME/projects_d" ]; then
    echo "✅ Symlink created: $HOME/projects_d -> $(readlink $HOME/projects_d)"
else
    echo "❌ Symlink not found"
fi
echo ""

echo "=== NEXT STEPS ==="
echo "If everything looks good above:"
echo "1. Start your RAG system: docker-compose up -d"
echo "2. Check services: docker-compose ps"
echo "3. Open VS Code and navigate to: /mnt/d/projects/rag"
echo ""
echo "If you see any ❌ errors above, check the troubleshooting section."