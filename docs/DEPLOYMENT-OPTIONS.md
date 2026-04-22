# Deployment Options & Methods

Choose the deployment method that best fits your needs.

## Deployment Methods Comparison

| Method | Setup Time | Automation | Flexibility | Recommended For |
|--------|-----------|-----------|-----------|---|
| **Azure Deploy Button** | 5 min | ✅ Full | ⭐⭐ Limited | Non-technical users, MVP |
| **GitHub Actions** | 10 min | ✅✅ Full auto | ⭐⭐⭐ High | Developers, continuous deployment |
| **Terraform CLI** | 15 min | ⭐ Manual apply | ⭐⭐⭐ Very high | Infrastructure engineers, multi-env |
| **Azure Portal GUI** | 30 min | ❌ Manual | ⭐ Very limited | Learning, one-off testing |

---

## Method 1: Deploy to Azure Button (Recommended)

### Overview
One-click deployment from GitHub directly to Azure Portal.

### Prerequisites
- Azure subscription
- GitHub account (already have code there)

### Steps

1. **Click Deploy Button** (in README.md)
   - Opens Azure Portal pre-configured

2. **Fill in Parameters**
   - Project name: `rag-prod`
   - Region: Select nearest to you
   - Groq API Key: Paste from https://console.groq.com/keys
   - Mistral API Key: Paste from https://console.mistral.ai/api-keys/

3. **Review + Create**
   - Confirm settings
   - Click "Create"

4. **Wait for Deployment**
   - Status visible in Azure Portal
   - 3-5 minutes typical

5. **Access Resources**
   - App Service URL: https://<name>.azurewebsites.net
   - Click → Open UI

### Pros
- ✅ No CLI required
- ✅ Visual parameter input
- ✅ Full validation before deployment
- ✅ Fastest for non-technical users

### Cons
- ❌ Limited customization (only exposed parameters)
- ❌ Harder to modify after deploy
- ❌ Cannot change resource names

### Post-Deployment
GitHub Actions still manages updates:
1. Edit `docs/` folder
2. Push to GitHub
3. GitHub Actions auto-redeploys

---

## Method 2: GitHub Actions (Full CI/CD)

### Overview
Fully automated deployment pipeline. Code push triggers infrastructure provisioning, build, and deployment.

### Prerequisites
- GitHub repository
- Azure subscription
- GitHub Secrets configured (see Phase 5)

### Setup

1. **Create GitHub Secrets** (Settings → Secrets and variables)
   - `AZURE_SUBSCRIPTION_ID`: Your Azure sub ID
   - `AZURE_TENANT_ID`: Your tenant ID
   - `AZURE_CLIENT_ID`: Service principal ID
   - `AZURE_CLIENT_SECRET`: Service principal secret
   - `LITELLM_GROQ_API_KEY`: From Groq console
   - `LITELLM_MISTRAL_API_KEY`: From Mistral console
   - `QDRANT_ADMIN_KEY`: Generate secure random key

2. **Create Service Principal** (for Terraform)
   ```bash
   az ad sp create-for-rbac \
     --name "rag-azure-sp" \
     --role Contributor \
     --scopes /subscriptions/<SUBSCRIPTION_ID>
   ```

3. **Workflow Ready**
   - `.github/workflows/deploy.yml` included in repo
   - Automatically runs on push to `main` branch

### Deployment Process

```
Your local dev
  ↓
git push to main
  ↓
GitHub Actions triggers
  ├─ Lint & test code
  ├─ Build Docker image
  ├─ Push to Container Registry
  ├─ Terraform init & plan
  ├─ Manual approval (optional)
  ├─ Terraform apply
  ├─ Deploy backend to App Service
  ├─ Deploy frontend to Blob Storage
  ├─ Run ingestion pipeline
  ├─ Smoke tests
  └─ Notify results
  ↓
Live deployment
```

### Trigger Options

**Automatic (on every push)**
```yaml
on:
  push:
    branches: [main]
```

**Manual (workflow dispatch)**
```yaml
on:
  workflow_dispatch:
```

**Scheduled (nightly)**
```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
```

### Pros
- ✅ Fully automated
- ✅ Consistent deployments
- ✅ Easy rollback (revert commit)
- ✅ Audit trail (GitHub actions logs)
- ✅ Team collaboration (code review before deploy)

### Cons
- ❌ Requires setup (service principal, secrets)
- ❌ GitHub free tier has limits (2000 min/month)
- ❌ Slightly more complex for beginners

### Manual Approval (Optional)

Add approval step before production deploy:

```yaml
deploy:
  runs-on: ubuntu-latest
  needs: test
  environment: production
  steps:
    - name: Manual approval required
      run: echo "Waiting for approval..."
```

Then use GitHub Environments to require manual approval.

---

## Method 3: Terraform CLI (Advanced)

### Overview
Direct infrastructure provisioning using Terraform. Full control and customization.

### Prerequisites
- Terraform installed (`terraform version`)
- Azure CLI installed (`az --version`)
- Logged into Azure (`az login`)
- API keys ready (Groq, Mistral)

### Steps

1. **Clone Repository**
   ```bash
   git clone https://github.com/<org>/rag-azure.git
   cd rag-azure/terraform
   ```

2. **Initialize Terraform**
   ```bash
   terraform init
   ```

3. **Create `.tfvars` File**
   ```bash
   cat > terraform.tfvars << EOF
   azure_region           = "eastus"
   app_name              = "rag-prod"
   litellm_groq_api_key  = "your-key-here"
   litellm_mistral_api_key = "your-key-here"
   qdrant_admin_key      = "your-secure-key"
   EOF
   ```

4. **Plan Deployment**
   ```bash
   terraform plan -out=tfplan
   ```
   Review output to verify what will be created.

5. **Apply Configuration**
   ```bash
   terraform apply tfplan
   ```
   Wait 3-5 minutes for all resources.

6. **Get Outputs**
   ```bash
   terraform output app_service_url
   terraform output qdrant_endpoint
   ```

### Directory Structure

```
terraform/
├── main.tf              # Resource definitions
├── variables.tf         # Input variables
├── outputs.tf           # Export values
├── terraform.tfvars     # Your values (don't commit!)
├── .terraform/          # Terraform cache (git-ignored)
├── .tfstate files       # State (git-ignored, back up!)
└── modules/
    ├── app_service/
    ├── aci_qdrant/
    ├── storage/
    └── networking/
```

### Common Commands

```bash
# Initialize (one-time)
terraform init

# Format code
terraform fmt -recursive

# Validate syntax
terraform validate

# Plan changes (dry-run)
terraform plan

# Apply changes
terraform apply

# View current state
terraform show

# Destroy all resources
terraform destroy
```

### State Management

Terraform maintains `.tfstate` file (contains all resource info).

**⚠️ Important:**
- Don't commit `.tfstate` to Git!
- Back up `.tfstate` file
- For team access, use Terraform Cloud or Azure Blob Backend

**Remote State (recommended for teams)**
```bash
# Initialize remote state in Azure
terraform init -backend-config="resource_group_name=rag-prod" \
               -backend-config="storage_account_name=rag1234" \
               -backend-config="container_name=tfstate" \
               -backend-config="key=terraform.tfstate"
```

### Pros
- ✅ Complete control
- ✅ Easy to customize resources
- ✅ Reproducible infrastructure
- ✅ Version control infrastructure
- ✅ Multi-environment support

### Cons
- ❌ Steeper learning curve
- ❌ Requires local tools (Terraform, Azure CLI)
- ❌ More manual steps
- ❌ State file management complexity

### Rollback

```bash
# View previous state versions
terraform state list
terraform state show

# Rollback to previous version
git checkout HEAD~1  # Revert commit
terraform plan       # Review changes
terraform apply
```

---

## Method 4: Azure Portal GUI (Manual)

### Overview
Point-and-click resource creation in Azure Portal.

### Prerequisites
- Azure subscription
- Azure Portal access

### Resources to Create Manually

1. **Resource Group**
   - Name: rag-prod
   - Region: eastus (or nearest)

2. **App Service Plan**
   - Tier: B1
   - OS: Linux
   - Region: same as resource group

3. **App Service**
   - Runtime: Docker (Linux)
   - Container image: your-registry.azurecr.io/rag-backend:latest

4. **Container Instances**
   - Image: qdrant/qdrant:latest
   - CPU: 1
   - Memory: 1GB
   - Port: 6333

5. **Storage Account**
   - Tier: Standard
   - Replication: LRS
   - Enable static site hosting

6. **Optional: PostgreSQL Database**
   - Tier: B_Standard_B1s
   - Storage: 32 GB

### Pros
- ✅ Learning-friendly (visual)
- ✅ 1-time manual process

### Cons
- ❌ Very time-consuming (30 min+)
- ❌ Error-prone (manual configuration)
- ❌ Hard to reproduce
- ❌ Not recommended for production

Only use this for learning. Use Deploy button or Terraform for real deployments.

---

## Comparison Matrix

| Requirement | Deploy Button | GitHub Actions | Terraform CLI | Azure Portal |
|---|---|---|---|---|
| **Non-technical user?** | ✅✅✅ | ⭐ | ❌ | ✅ |
| **Developer?** | ✅ | ✅✅✅ | ✅✅ | ⭐ |
| **Infrastructure engineer?** | ❌ | ✅ | ✅✅✅ | ❌ |
| **Setup time** | 5 min | 10 min | 15 min | 30+ min |
| **Customization** | Limited | Full | Full | Full |
| **Reproducibility** | ✅ | ✅✅✅ | ✅✅✅ | ❌ |
| **Team collaboration** | ⭐ | ✅✅✅ | ✅✅ | ❌ |
| **Cost** | Free | Free | Free | Free |

---

## Multi-Environment Deployment

### Recommended Setup

```
Production (prod)
├─ App Service: S1 ($100/mo)
├─ Qdrant: Large ACI
└─ Alerts: Enabled

Staging (staging)
├─ App Service: B2 ($50/mo)
├─ Qdrant: Medium ACI
└─ Manual deploy

Development (dev)
├─ Local docker-compose
└─ Free (laptop)
```

### Using Terraform for Multi-Env

```bash
# Deploy to staging
terraform workspace new staging
terraform apply -var-file=staging.tfvars

# Deploy to production
terraform workspace new production
terraform apply -var-file=production.tfvars

# List environments
terraform workspace list

# Switch environments
terraform workspace select staging
```

---

## Rollback Strategy

### If Deployment Fails

**Using Deploy Button:**
- Delete resource group (Azure Portal)
- Click Deploy button again

**Using GitHub Actions:**
```bash
# Revert last commit
git revert HEAD
git push

# GitHub Actions automatically redeploys previous version
```

**Using Terraform:**
```bash
# View history
terraform state list
git log

# Rollback to previous commit
git checkout HEAD~1
terraform apply
```

---

## Monitoring & Verification

After deploying (any method):

1. **Check Health**
   ```bash
   curl https://<your-app>.azurewebsites.net/health
   ```

2. **View Logs**
   ```bash
   az webapp log tail --name <app-name> --resource-group rag-prod
   ```

3. **Test Query**
   ```bash
   curl -X POST https://<your-app>.azurewebsites.net/query \
     -H "Content-Type: application/json" \
     -d '{"query": "test", "top_k": 5}'
   ```

4. **Monitor Costs**
   - Azure Portal → Cost Management
   - Set alerts at 50%, 75%, 90%

---

## Recommendation for Your Use Case

- **First time?** → **Deploy Button** (5 min, no setup)
- **Production**? → **GitHub Actions** (fully automated)
- **Large infrastructure**? → **Terraform CLI** (full control)

---

For issues with deployment, see [Troubleshooting](FAQ.md#troubleshooting).
