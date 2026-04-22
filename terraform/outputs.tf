"""Terraform outputs."""
output "resource_group_id" {
  description = "Resource group ID"
  value       = azurerm_resource_group.rg.id
}

output "app_service_url" {
  description = "URL of the App Service"
  value       = "https://${azurerm_linux_web_app.backend.default_hostname}"
}

output "app_service_name" {
  description = "Name of the App Service"
  value       = azurerm_linux_web_app.backend.name
}

output "storage_account_name" {
  description = "Name of the Storage Account"
  value       = azurerm_storage_account.storage.name
}

output "storage_account_url" {
  description = "Primary blob service endpoint"
  value       = azurerm_storage_account.storage.primary_blob_endpoint
}

output "static_site_url" {
  description = "URL of the static website"
  value       = "https://${azurerm_storage_account.storage.primary_web_endpoint}/"
}

output "qdrant_host" {
  description = "Qdrant container host"
  value       = azurerm_container_group.qdrant.fqdns[0]
}

output "qdrant_port" {
  description = "Qdrant container port"
  value       = 6333
}

output "qdrant_connection_string" {
  description = "Qdrant connection string"
  value       = "http://${azurerm_container_group.qdrant.fqdns[0]}:6333"
}

output "deployment_info" {
  description = "Summary of deployment"
  value = {
    resource_group        = azurerm_resource_group.rg.name
    region                = azurerm_resource_group.rg.location
    app_service_url       = "https://${azurerm_linux_web_app.backend.default_hostname}"
    static_site_url       = "https://${azurerm_storage_account.storage.primary_web_endpoint}/"
    qdrant_endpoint       = "http://${azurerm_container_group.qdrant.fqdns[0]}:6333"
    next_steps = [
      "1. Set Azure secrets in GitHub Actions for auto-deployment",
      "2. Push code to trigger ingestion: 'git push'",
      "3. Monitor deployment in GitHub Actions",
      "4. Open static site URL to access UI",
    ]
  }
}
