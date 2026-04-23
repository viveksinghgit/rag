"""Terraform main configuration."""

# Create resource group
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.azure_region

  tags = local.common_tags
}

# App Service Plan
resource "azurerm_service_plan" "plan" {
  name                = "${local.resource_name_suffix}-plan"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = var.app_service_sku

  tags = local.common_tags
}

# App Service (FastAPI Backend)
resource "azurerm_linux_web_app" "backend" {
  name                = "${local.resource_name_suffix}-app"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.plan.id

  https_only = true

  site_config {
    minimum_tls_version = "1.2"

    # After first deploy, update this to point to your built backend image
    # e.g. "ghcr.io/viveksinghgit/rag/backend:latest" or an ACR image
    docker_image_name  = "viveksinghgit/rag-backend:latest"
    docker_registry_url = "https://index.docker.io"
  }

  app_settings = {
    DEBUG                              = "false"
    ENVIRONMENT                        = var.environment
    QDRANT_HOST                        = azurerm_container_group.qdrant.fqdns[0]
    QDRANT_PORT                        = "6333"
    QDRANT_COLLECTION_NAME             = "documents"
    QDRANT_ADMIN_KEY                   = var.qdrant_admin_key
    QDRANT_VECTOR_SIZE                 = "1024"
    QDRANT_RECREATE_ON_VECTOR_MISMATCH = "false"
    LLM_PROVIDER                       = "litellm"
    EMBEDDING_PROVIDER                 = "litellm"
    LITELLM_GROQ_API_KEY               = var.litellm_groq_api_key
    LITELLM_MISTRAL_API_KEY            = var.litellm_mistral_api_key
    LITELLM_EMBEDDING_MODEL            = "mistral/mistral-embed"
    LITELLM_LLM_MODEL                  = "groq/qwen/qwen3-32b"
    RETRIEVAL_LIMIT                    = "5"
    SIMILARITY_THRESHOLD               = "0.5"
    CONTEXT_WINDOW_LIMIT               = "2000"
    WEBSITES_PORT                      = "8000"
  }

  logs {
    http_logs {
      file_system {
        retention_in_days = 7
      }
    }
  }

  tags = local.common_tags

  depends_on = [azurerm_container_group.qdrant]

  lifecycle {
    ignore_changes = [
      site_config[0].docker_image_name,
      site_config[0].docker_registry_url,
    ]
  }
}

# Storage Account
resource "azurerm_storage_account" "storage" {
  name                     = replace("${local.resource_name_suffix}sa", "-", "")
  location                 = azurerm_resource_group.rg.location
  resource_group_name      = azurerm_resource_group.rg.name
  account_tier             = "Standard"
  account_replication_type = "LRS"
  https_traffic_only_enabled = true
  min_tls_version          = "TLS1_2"

  tags = local.common_tags
}

# Blob Container for documents
resource "azurerm_storage_container" "docs" {
  name                  = "documents"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}

# File Share for Qdrant persistent storage (used by Container Instances volume mount)
resource "azurerm_storage_share" "qdrant" {
  name                 = "qdrant-storage"
  storage_account_name = azurerm_storage_account.storage.name
  quota                = var.qdrant_storage_gb
}

# Enable static website on storage account (hosts the React frontend)
resource "azurerm_storage_account_static_website" "frontend" {
  storage_account_id = azurerm_storage_account.storage.id
  index_document     = "index.html"
  error_404_document = "index.html"
}

# Container Instances for Qdrant
resource "azurerm_container_group" "qdrant" {
  name                = "${local.resource_name_suffix}-qdrant"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  ip_address_type     = "Public"
  dns_name_label      = "${local.resource_name_suffix}-qdrant"
  os_type             = "Linux"

  container {
    name   = "qdrant"
    image  = "qdrant/qdrant:latest"
    cpu    = var.qdrant_cpu
    memory = var.qdrant_memory_gb

    ports {
      port     = 6333
      protocol = "TCP"
    }

    secure_environment_variables = {
      QDRANT__SERVICE__API_KEY = var.qdrant_admin_key
    }

    volume {
      name                 = "qdrant-storage"
      mount_path           = "/qdrant/storage"
      read_only            = false
      storage_account_name = azurerm_storage_account.storage.name
      storage_account_key  = azurerm_storage_account.storage.primary_access_key
      share_name           = azurerm_storage_share.qdrant.name
    }
  }

  tags = local.common_tags

  depends_on = [azurerm_storage_account.storage]
}

# Network Security Group
resource "azurerm_network_security_group" "nsg" {
  name                = "${local.resource_name_suffix}-nsg"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowHTTP"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = local.common_tags
}
