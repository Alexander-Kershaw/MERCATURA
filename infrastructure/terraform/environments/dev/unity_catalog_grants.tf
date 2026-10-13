resource "databricks_grant" "data_engineers_catalog" {
  catalog = databricks_catalog.dev.name

  principal = data.databricks_group.data_engineers.display_name

  privileges = [
    "USE_CATALOG",
  ]
}

resource "databricks_grant" "data_engineers_landing_schema" {
  schema = databricks_schema.landing.id

  principal = data.databricks_group.data_engineers.display_name

  privileges = [
    "USE_SCHEMA",
  ]
}

resource "databricks_grant" "data_engineers_source_files" {
  volume = databricks_volume.source_files.id

  principal = data.databricks_group.data_engineers.display_name

  privileges = [
    "READ_VOLUME",
  ]
}