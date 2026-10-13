locals {
  common_tags = {
    project      = "meridian"
    organisation = "mercatura"
    environment  = "dev"
    managed_by   = "terraform" # initially CLI managed, then managed by Terraform after the configuration matches what already exists in Azure from bootstrap
    purpose      = "data-platform"
  }

  subscription_scope = "/subscriptions/${var.subscription_id}"

  resource_group_id = "${local.subscription_scope}/resourceGroups/${var.resource_group_name}"

  storage_account_id = "${local.resource_group_id}/providers/Microsoft.Storage/storageAccounts/${var.storage_account_name}"

  access_connector_id = "${local.resource_group_id}/providers/Microsoft.Databricks/accessConnectors/${var.access_connector_name}"

  managed_storage_url = "abfss://managed@${azurerm_storage_account.data.name}.dfs.core.windows.net/"

  landing_storage_url = "abfss://landing@${azurerm_storage_account.data.name}.dfs.core.windows.net/"

  catalog_storage_root = "${local.managed_storage_url}mercatura_dev"

  source_files_storage_location = "${local.landing_storage_url}source_files"
}