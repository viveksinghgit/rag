# Local Development & Deployment Guide

## Current Status

✅ **Code Complete**
- All 9 Python modules compile without errors
- FastAPI backend fully implemented
- RAG pipeline orchestration complete
- React frontend ready
- Terraform infrastructure-as-code validated
- Comprehensive documentation included

🟡 **Docker Setup Pending**
- Docker daemon requires socket permission fixes
- Once permissions configured, `docker-compose up --build` will work

---

## Prerequisites & Troubleshooting

### Issue: "Docker daemon socket permission denied"

This occurs because the Docker socket (`/var/run/docker.sock`) is owned by root and requires elevated permissions.

#### Solution 1: Add User to Docker Group (Recommended)

```bash
# Create docker group if it doesn't exist
sudo groupadd docker 2>/dev/null || true

# Add current user to docker group
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Verify (should not need sudo)
docker ps
```

After this, log out completely and log back in for the group change to persist.

#### Solution 2: Fix Socket Permissions Temporarily

```bash
# Make socket accessible to all users
sudo chmod 666 /var/run/docker.sock

# Test
docker ps
```

⚠️ This resets on Docker daemon restart - Solution 1 is permanent.

#### Solution 3: Configure Passwordless Sudo for Docker (Advanced)

```bash
# Add to sudoers (nano or vim)
sudo visudo

# Add this line at the end:
%docker ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose

# Then use:
sudo docker-compose up --build
```

---

## Step-by-Step Setup

### 1. Install Docker (if not already installed)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Start service
sudo systemctl start docker
sudo systemctl enable docker
```

**macOS/Windows:**
Download [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 2. Fix Docker Permissions (Required)

Choose one solution from the troubleshooting section above. **Solution 1 is recommended.**

After fixing permissions, verify:
```bash
docker ps
```

Should show running containers (may be empty initially).

### 3. Configure API Keys

Edit `backend/.env`:

```bash
nano backend/.env
```

Replace placeholder values with real API keys:

```env
# From https://console.groq.com/keys
LITELLM_GROQ_API_KEY=gsk_YOUR_REAL_KEY_HERE

# From https://console.mistral.ai/api-keys/
LITELLM_MISTRAL_API_KEY=YOUR_REAL_KEY_HERE

# Generate a secure ID or use UUID
QDRANT_ADMIN_KEY=your-secure-uuid-or-key
```

### 4. Start Services

From project root (`/home/vs/projects/rag`):

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up --build -d

# View logs
docker-compose logs -f
```

First build takes 5-10 minutes. Subsequent runs are faster.

### 5. Access Services

Once all services show "ready" or "running":

- **Backend API**: http://localhost:8000/docs
- **Raw API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Qdrant Admin**: http://localhost:6333

---

## Testing the Setup

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "app_name": "RAG Azure Backend",
  "version": "0.1.0",
  "environment": "development"
}
```

### Configuration Endpoint
```bash
curl http://localhost:8000/config
```

### Ingest Documents
```bash
curl -X POST http://localhost:8000/ingest
```

### Query RAG Pipeline (requires valid API keys)
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 5
  }'
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "permission denied" on docker.sock | User not in docker group | Run Solution 1 from troubleshooting |
| "No matching distribution found" | Old pip cache | `docker-compose down -v && docker-compose up --build` |
| "Bind for 0.0.0.0:8000 failed" | Port already in use | Change port in docker-compose.yml |
| OutOfMemory | Docker needs more resources | Increase memory in Docker preferences |
| Container exits immediately | Check logs with `docker-compose logs` | See logs section below |

---

## Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f qdrant
docker-compose logs -f frontend

# Last N lines
docker-compose logs --tail=50

# With timestamps
docker-compose logs -f --timestamps
```

---

## Development Workflow

### Frontend Development (Hot Reload)
```bash
# React automatically reloads when files in frontend/src/ change
# View at localhost:3000

# Make changes in frontend/src/
nano frontend/src/App.jsx

# Save - browser reloads automatically
```

### Backend Development
```bash
# After modifying backend Python code
docker-compose restart backend

# Or full rebuild
docker-compose down
docker-compose up --build
```

### Vector Database
```bash
# Access Qdrant admin panel
# Browse to http://localhost:6333/

# Or use curl
curl http://localhost:6333/collections
```

---

## Stopping & Cleanup

```bash
# Stop all services (keep volumes/data)
docker-compose stop

# Restart
docker-compose start

# Stop and remove containers (keep volumes)
docker-compose down

# Full cleanup (remove everything including data)
docker-compose down -v

# Remove specific service
docker-compose rm backend
```

---

## Production Deployment

Once local development works, deploy to Azure:

1. **Using Terraform**
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```
   See [terraform/README.md](terraform/README.md)

2. **Using Azure Deploy Button**
   - Coming in Phase 6

3. **Using GitHub Actions**
   - Coming in Phase 5

---

## Verifying Complete Installation

After `docker-compose up --build` succeeds, you should see:

```
backend-1   | INFO:     Application startup complete
qdrant-1    | INFO:     Server started on 0.0.0.0:6333
frontend-1  | Local:   http://localhost:3000
```

Then test:

```bash
# All three should succeed
curl http://localhost:8000/health
curl http://localhost:3000/
curl http://localhost:6333/collections
```

---

## Next Phases

- ✅ Phase 1-4: Complete (all code ready)
- ⏳ Phase 5: GitHub Actions CI/CD
- ⏳ Phase 6: Deploy to Azure Button
- ⏳ Phase 7: Advanced Documentation
- ⏳ Phase 8: Testing & Monitoring
- ⏳ Phase 9: Production Hardening

---

## Support & Documentation

- [COST-BREAKDOWN.md](COST-BREAKDOWN.md) - Pricing details
- [README-ARCHITECTURE.md](README-ARCHITECTURE.md) - Technical architecture
- [FAQ.md](FAQ.md) - Common questions
- [DEPLOYMENT-OPTIONS.md](DEPLOYMENT-OPTIONS.md) - Deployment strategies
- [LOCAL-DEVELOPMENT.md](LOCAL-DEVELOPMENT.md) - Local dev details

