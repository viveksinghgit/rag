#!/bin/bash
# WSL and Docker Optimization Script for D Drive
# Run this AFTER moving WSL to D drive

echo "=== WSL & Docker Optimization for D Drive ==="

# Create Docker data directory on D drive
echo "Creating Docker data directory on D drive..."
sudo mkdir -p /mnt/d/docker-data
sudo chown -R $USER:$USER /mnt/d/docker-data

# Configure Docker to use D drive
echo "Configuring Docker daemon..."
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "data-root": "/mnt/d/docker-data"
}
EOF

# Move project to D drive
echo "Moving RAG project to D drive..."
if [ ! -d "/mnt/d/projects" ]; then
    cp -r /home/vs/projects /mnt/d/
    echo "Project copied to /mnt/d/projects"
fi

# Create symlink for easy access
echo "Creating symlink for easy access..."
ln -sf /mnt/d/projects ~/projects_d

echo "=== Optimization Complete ==="
echo "Next steps:"
echo "1. Update VS Code workspace to: /mnt/d/projects/rag"
echo "2. Update docker-compose.yml volume paths to use /mnt/d/..."
echo "3. Restart Docker: sudo systemctl restart docker"
echo "4. Test your RAG setup"