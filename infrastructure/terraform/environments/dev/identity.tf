data "databricks_current_user" "me" {}

data "databricks_group" "platform_admins" {
  display_name = "mercatura-dev-platform-admins"
}

data "databricks_group" "data_engineers" {
  display_name = "mercatura-dev-data-engineers"
}