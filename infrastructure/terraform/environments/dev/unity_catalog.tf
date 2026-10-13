resource "databricks_storage_credential" "dev" {
  name = "mercatura_dev_storage"

  azure_managed_identity {
    access_connector_id = azurerm_databricks_access_connector.unity_catalog.id
  }

  comment = "Managed identity for Project Meridian development ADLS access."

  owner = data.databricks_group.platform_admins.display_name
}


resource "databricks_external_location" "managed" {
  name = "mercatura_dev_managed"

  url = local.managed_storage_url

  credential_name = databricks_storage_credential.dev.name

  comment = "Managed storage root for Project Meridian development data."

  owner = data.databricks_group.platform_admins.display_name
}


resource "databricks_external_location" "landing" {
  name = "mercatura_dev_landing"

  url = local.landing_storage_url

  credential_name = databricks_storage_credential.dev.name

  comment = "External landing storage for Mercatura development source files."

  owner = data.databricks_group.platform_admins.display_name
}


resource "databricks_catalog" "dev" {
  name = "mercatura_dev"

  storage_root = local.catalog_storage_root

  comment = "Development catalog for the Mercatura Data Platform."

  owner = data.databricks_group.platform_admins.display_name

  lifecycle {
    prevent_destroy = true
  }
}


resource "databricks_schema" "landing" {
  name         = "landing"
  catalog_name = databricks_catalog.dev.name

  comment = "Governed interface for externally produced source files."

  owner = data.databricks_group.platform_admins.display_name

  properties = {
    owner = "root"
  }

  lifecycle {
    prevent_destroy = true
  }
}


resource "databricks_volume" "source_files" {
  name = "source_files"

  catalog_name = databricks_catalog.dev.name
  schema_name  = databricks_schema.landing.name

  volume_type = "EXTERNAL"

  storage_location = local.source_files_storage_location

  comment = "Landing area for source-system files delivered to Project Meridian."

  owner = data.databricks_group.platform_admins.display_name

  lifecycle {
    prevent_destroy = true
  }
}