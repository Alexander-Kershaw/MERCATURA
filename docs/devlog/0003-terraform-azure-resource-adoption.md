# Devlog 0003 — Terraform Azure Resource Adoption

## Goal

Introduce Infrastructure as Code (IAC) without recreating the working Project Meridian development environment that was already accompished via the Azure CLI as the inital bootstrap environment.

## Resources adopted

- development resource group
- ADLS Gen2 storage account
- `managed` container
- `landing` container
- Databricks Access Connector
- Storage Blob Data Contributor role assignment

## Databricks workspace

The serverless Azure Databricks workspace remains an AzureRM data source rather than a Terraform managed resource.

The current AzureRM workspace resource does not expose the serverless
`compute_mode` property required to describe the existing workspace faithfully.

Therefore the Databricks workspace will not be forced into Terraform ownership if I cant recreate my current workspace authentically.

## Import result

Initial plan:

```text
6 to import
0 to add
0 to change
0 to destroy
```

All the resouces were imported successfully and subsequent running of terraform plan did not indicate any infrastructure drift, implying that the provisioned infrastructure managed by terraform after application matches that of the initial bootstrapped infrastructure managed by Azure CLI faithfully.

## First Terraform Managed Change

To reflect the change in infrastructure management from Azure CLI to terraform, the resource tags were changed from:

```txt
managed_by = cli
```

to:

```txt
managed_by = terraform
```

This was verified in Azure web interface, CLI, and terraform state, and a reviewed terraform plan.

## Core Concepts Encountered

The terraform configuration describes the desired infrastructure state. 

A terraform state effectively maps terraform resourse addresses to the real infrastructure provisioned (in Azure in this case) and stores provider observations about those resource.

Imports adopt an existing resource into the terraform state rather than creating it. The import approach was done since the resources already existed in Azure as they were originally provisioned with Azure CLI during bootstrapping.

Data source reads an existing resource without taking lifecycle ownership from it. 

The terraform plan shows the proposed transition from the current terraform state to the desired state. If the terraform plan is valid and after review, terraform apply is used to execute the reviewed infrastructure state transition.

## Verification

- The import plan contained no adds, changes, or destroys, reflecting that the terraform state complements the prexisting Azure resource instrastructure that was previously provisioned
- The post import plan returned no changes, so the terraform state after importing resources into terraform, matched the desired state
- tag-only plan contained no resource replacement, so the core infrastructure correctly remained unchanged apart from changing tags representing the change in management from CLI to terraform 
- post-apply state returned no changes
- Azure showed the updated managed by terraform tag as intended.

## Next Step

I want to move the terraform state from the local workstation to a dedicated Azure Blob remote backend with state locking before augmenting to the terraform managed platform resources.