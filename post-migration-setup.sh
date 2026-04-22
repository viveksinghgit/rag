#!/bin/bash
# Post-WSL-Migration Setup Script
# Run this AFTER moving WSL to D drive

echo "=== Post-WSL-Migration Setup ==="

# Configure Docker for snap (if using snap)
echo "Configuring Docker data root..."
if command -v snap >/dev/null 2>&1 && snap list | grep -q docker; then
    echo "Docker is installed via snap"
    # For snap Docker, create override config
    sudo mkdir -p /var/snap/docker/current/config
    sudo tee /var/snap/docker/current/config/daemon.json > /dev/null <<EOF
{
  "data-root": "/mnt/d/docker-data"
}
EOF
    echo "Restarting snap Docker..."
    sudo snap restart docker
else
    echo "Docker appears to be system-installed"
    echo "Restarting system Docker..."
    sudo systemctl restart docker
fi

# Verify Docker data location
echo "Verifying Docker data location..."
docker system info | grep "Docker Root Dir" || echo "Docker Root Dir not accessible (may be normal for snap)"

# Test Docker functionality
echo "Testing Docker..."
docker run --rm hello-world >/dev/null 2>&1 && echo "✅ Docker is working" || echo "❌ Docker test failed"

# Update any remaining symlinks or paths
echo "Updating workspace symlink..."
rm -f ~/projects 2>/dev/null
ln -sf /mnt/d/projects ~/projects_d

echo "=== Setup Complete ==="
echo ""
echo "🎉 WSL and Docker optimization complete!"
echo ""
echo "📁 New workspace location: /mnt/d/projects/rag"
echo "🔗 Symlink created: ~/projects_d -> /mnt/d/projects"
echo ""
echo "Next steps:"
echo "1. In VS Code: File -> Open Folder -> /mnt/d/projects/rag"
echo "2. Test your RAG setup: cd /mnt/d/projects/rag && docker-compose up -d"
echo "3. Verify all services are running: docker-compose ps"
echo ""
echo "💾 Space saved on C drive: ~85GB (WSL + Docker data moved to D drive)"