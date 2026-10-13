# Need the azure provider to be loaded into terraform, using most recent terraform version too 

terraform {
  required_version = "~> 1.16.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.9"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.134"
    }
  }
}