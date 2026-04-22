"""Terraform input variables."""
terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  
  skip_provider_registration = false
}

# Variables
variable "azure_region" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "app_name" {
  description = "Base name for all resources (3-24 chars, lowercase alphanumeric)"
  type        = string
  validation {
    condition     = length(var.app_name) >= 3 && length(var.app_name) <= 24 && can(regex("^[a-z0-9-]*$", var.app_name))
    error_message = "App name must be 3-24 characters, lowercase alphanumeric and hyphens only."
  }
}

variable "environment" {
  description = "Environment name (dev/staging/prod)"
  type        = string
  default     = "prod"
}

# LLM & LiteLLM Configuration
variable "litellm_groq_api_key" {
  description = "Groq API key for LiteLLM"
  type        = string
  sensitive   = true
}

variable "litellm_mistral_api_key" {
  description = "Mistral API key for LiteLLM (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

# Qdrant Configuration
variable "qdrant_admin_key" {
  description = "Qdrant admin key for security"
  type        = string
  sensitive   = true
}

# Resource Configuration
variable "app_service_sku" {
  description = "App Service SKU"
  type        = string
  default     = "B1"
  validation {
    condition     = contains(["B1", "B2", "B3", "S1", "S2", "P1V2"], var.app_service_sku)
    error_message = "Valid SKUs: B1, B2, B3, S1, S2, P1V2"
  }
}

variable "qdrant_cpu" {
  description = "CPU cores for Qdrant container"
  type        = number
  default     = 1
}

variable "qdrant_memory_gb" {
  description = "Memory (GB) for Qdrant container"
  type        = number
  default     = 1
}

variable "qdrant_storage_gb" {
  description = "Storage size (GB) for Qdrant"
  type        = number
  default     = 10
}

# Tagging
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    project     = "RAG-Azure"
    managedBy   = "Terraform"
    environment = "prod"
  }
}

# Local values
locals {
  resource_name_suffix = "${var.app_name}-${var.environment}"
  common_tags = merge(
    var.tags,
    {
      environment = var.environment
      lastUpdated = timestamp()
    }
  )
}
