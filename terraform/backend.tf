# Terraform Backend Configuration Example
# Uncomment and fill in to use remote state in Azure Blob Storage

# terraform {
#   backend "azurerm" {
#     resource_group_name  = "rag-terraform-backend"
#     storage_account_name = "ragterraformstate"
#     container_name       = "tfstate"
#     key                  = "terraform.tfstate"
#   }
# }
