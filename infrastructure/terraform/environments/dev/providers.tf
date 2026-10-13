# Storage account has shared key access disabled
# So, terraform cant rely on account keys when interacting with the storage data-plane APIs

provider "azurerm" {
  features {}
  subscription_id     = var.subscription_id
  storage_use_azuread = true # Use Microsoft Entra ID (Azure AD) for authentication instead of account keys
}

provider "databricks" {
  profile = "mercatura-dev"
}
