resource "azurerm_resource_group" "dev" {
  name     = var.resource_group_name
  location = var.location

  tags = local.common_tags
}

resource "azurerm_storage_account" "data" {
  name                = var.storage_account_name
  resource_group_name = azurerm_resource_group.dev.name
  location            = azurerm_resource_group.dev.location

  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  is_hns_enabled                  = true
  https_traffic_only_enabled      = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = false
  public_network_access           = "Enabled"

  tags = local.common_tags

  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_storage_container" "managed" {
  name                  = "managed"
  storage_account_id    = azurerm_storage_account.data.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "landing" {
  name                  = "landing"
  storage_account_id    = azurerm_storage_account.data.id
  container_access_type = "private"
}

resource "azurerm_databricks_access_connector" "unity_catalog" {
  name                = var.access_connector_name
  resource_group_name = azurerm_resource_group.dev.name
  location            = azurerm_resource_group.dev.location

  identity {
    type = "SystemAssigned"
  }

  tags = {
    project      = "meridian"
    organisation = "mercatura"
    environment  = "dev"
    managed_by   = "terraform"
    purpose      = "unity-catalog-storage"
  }
}

resource "azurerm_role_assignment" "unity_catalog_blob_data" {
  scope                = azurerm_storage_account.data.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.unity_catalog.identity[0].principal_id
}

data "azurerm_databricks_workspace" "dev" {
  name                = var.databricks_workspace_name
  resource_group_name = azurerm_resource_group.dev.name
}

