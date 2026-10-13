variable "subscription_id" {
  description = "Azure subscription ID containing the project Meridian dev resources"
  type        = string
}

variable "storage_account_name" {
  description = "The existing project Meridian dev ADLS Gen2 storage account"
  type        = string
}

variable "blob_role_assignment_id" {
  description = "The Azure resource ID of the existing Storage Blob Data Contributor role assignment for the project Meridian dev ADLS Gen2 storage account"
  type        = string
}

variable "resource_group_name" {
  description = "The project Meridian dev resource group name"
  type        = string
  default     = "rg-mercatura-dev-uks"
}

variable "location" {
  description = "The Azure region for the project Meridian dev resources"
  type        = string
  default     = "UK South"
}

variable "databricks_workspace_name" {
  description = "The existing project Meridian dev Databricks workspace name"
  type        = string
  default     = "dbw-mercatura-dev-uks"
}

variable "access_connector_name" {
  description = "Unity Catalog access connector name for the project Meridian dev Databricks workspace"
  type        = string
  default     = "ac-mercatura-dev-uks"
}

