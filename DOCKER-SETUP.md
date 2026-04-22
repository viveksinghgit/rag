# Docker Setup Guide

## Prerequisites

### 1. Install Docker & Docker Compose

**Linux:**
```bash
# Install Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Start Docker daemon
sudo systemctl start docker
sudo systemctl enable docker
```

**macOS/Windows:**
- Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop)

---

## Step 1: Configure Docker Permissions (Linux Users)

The Docker daemon socket requires root or docker group permissions. Choose one:

### Option A: Add User to Docker Group (Recommended)
```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Apply group changes (choose one)
newgrp docker
# OR log out and log back in
```

**Verify:**
```bash
docker ps
```
If it works without `sudo`, you're good to go!

### Option B: Use Sudo with Passwordless Docker (Alternative)
```bash
# Add docker commands to sudoers for passwordless execution
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose" | sudo tee /etc/sudoers.d/docker-rag

# Then run with sudo
sudo docker-compose up --build
```

---

## Step 2: Configure API Keys

Edit the `.env` file in `backend/` directory:
```bash
cd backend
nano .env  # or your preferred editor
```

Add your actual API keys:
```env
# Get from https://console.groq.com/keys
LITELLM_GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

# Get from https://console.mistral.ai/api-keys/
LITELLM_MISTRAL_API_KEY=xxxxxxxxxxxxxxxxxxxxx

# Qdrant (generate a UUID or use admin key)
QDRANT_ADMIN_KEY=your-secure-key-or-uuid
```

---

## Step 3: Build & Run Docker Services

From the project root (`/home/vs/projects/rag`):

```bash
# Build images and start services
docker-compose up --build

# Or if using sudo
sudo docker-compose up --build
```

This will:
1. ✓ Build the FastAPI backend image (~5-10 min first run)
2. ✓ Pull and start Qdrant vector database
3. ✓ Start React frontend dev server
4. ✓ Output logs from all services

---

## Step 4: Access Services

Once all services are running:

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Frontend**: http://localhost:3000
- **Qdrant**: http://localhost:6333

---

## Testing the Setup

### 1. Health Check
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

### 2. Get Configuration
```bash
curl http://localhost:8000/config
```

### 3. Ingest Sample Documents
```bash
curl -X POST http://localhost:8000/ingest
```

### 4. Send a Query (requires valid API keys)
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 5}'
```

---

## Common Issues

### "Permission denied" when accessing docker socket
**Solution:** Run the docker group configuration (Step 1, Option A) and restart your shell.

### "No matching distribution found for qdrant-client>=2.7.0"
**Solution:** This is already fixed in `requirements.txt`. Run with the latest code.

### Containers not starting
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Full rebuild
docker-compose down
docker-compose up --build
```

### Port already in use
Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### OutOfMemory errors
Docker might need more resources. In Docker Desktop:
- Settings → Resources → Increase Memory/CPUs
- For example: 4GB RAM, 2 CPUs minimum

---

## Stopping Services

```bash
# Stop all services (keep data)
docker-compose stop

# Stop and remove containers (keep volumes)
docker-compose down

# Stop and remove everything
docker-compose down -v
```

---

## Development Workflow

### Hot Reload Frontend
The React app automatically reloads on code changes in `frontend/src/`.

### Backend Changes Require Rebuild
After modifying backend Python code:
```bash
docker-compose restart backend
# or rebuild
docker-compose up --build backend
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f qdrant
docker-compose logs -f frontend
```

---

## Next Steps

1. ✓ Verify Docker is running with `docker ps`
2. ✓ Configure API keys in `.env`
3. ✓ Run `docker-compose up --build`
4. ✓ Test endpoints with curl or Swagger UI
5. ✓ Ingest documents and run queries
6. → Ready for Phase 5: GitHub Actions CI/CD

---

## For Production Deployment

See [DEPLOYMENT-OPTIONS.md](./DEPLOYMENT-OPTIONS.md) for:
- Azure Container Registry
- Azure App Service deployment
- Kubernetes setup
- Terraform automation
