output "storage_account_name" {
  description = "Project Meridian development ADLS Gen2 storage account."
  value       = azurerm_storage_account.data.name
}

output "access_connector_id" {
  description = "Azure resource ID of the Databricks Access Connector."
  value       = azurerm_databricks_access_connector.unity_catalog.id
}

output "access_connector_principal_id" {
  description = "Managed identity principal used by Unity Catalog."
  value       = azurerm_databricks_access_connector.unity_catalog.identity[0].principal_id
}

output "databricks_workspace_url" {
  description = "Existing Project Meridian Databricks workspace URL."
  value       = data.azurerm_databricks_workspace.dev.workspace_url
}