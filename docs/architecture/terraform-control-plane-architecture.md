# Terrafrom and Control-Plane Architecture

## Intentions

This documents serves to explain how Terraform interconnects and interacts with Azure, Azure Databricks, Unity Catalog, and with the Terrafrom state backend for the Mercatura Data Platform.

Note that this is an intermediate document and represents the final infrastructure architecture established at the time of the commit. Architectural decisions could mutate as progress towards the final product continues.

---

## Overall Architecture

The current architecture spans over four distinct funtional concernsL

```txt
Git repository
    │
    ▼
Terraform configuration
    │
    ├──────────────────────────────┐
    │                              │
    ▼                              ▼
AzureRM provider             Databricks provider
    │                              │
    ▼                              ▼
Azure Resource Manager       Databricks workspace API
    │                              │
    ▼                              ▼
Azure infrastructure         Unity Catalog resources

           Terraform state
                  │
                  ▼
       dedicated Azure Blob backend
```

Terrafrom represents the orchestration layer. Id does not mean that Azure and Databricks is collapsed into a singular platfrom. Terrafrom contains them as different providers, which call different control planes.

## Providers

#### AzureRM Provider

The AzureRM provider manages Azure infrastructure. The resources included at this point are:

- azurerm_resource_group.dev
- azurerm_storage_account.data
- azurerm_storage_container.managed
- azurerm_storage_container.landing
- azurerm_databricks_access_connector.unity_catalog
- azurerm_role_assignment.unity_catalog_blob_data

The AzureRM provider authenticates via my Azure CLI session where I have logged in with `az login`.

Basically, Terrafrom contains the AzureRM provider, which get context from my Azure CLI session, which is authenticated. This authenticated context connects to the Azure resource manager / Azure service APIs.

#### Databricks Provider

The Databricks provider manages workspace and Unity Catalog objects and uses the local OAuth profile `mercatura-dev`.

So Terrafrom has the Databricks provider, this connects to my OAuth profile which connects to the Azure Databricks workspace API.

Currently, the following Unity Catalog objects being managed by Terraform include:

- databricks_storage_credential.dev
- databricks_external_location.managed
- databricks_external_location.landing
- databricks_catalog.dev
- databricks_schema.landing
- databricks_volume.source_files

Terraform also manages specific Unity Catalog grants.

## Provider Dependency Graph

```txt
Azure storage account
        │
        ├── managed container
        └── landing container

Azure Access Connector
        │
        └── assigned managed identity
                 │
                 ▼
        Azure RBAC on ADLS
                 │
                 ▼
Unity Catalog storage credential
                 │
          ┌──────┴──────┐
          ▼             ▼
 managed external   landing external
    location           location
          │             │
          ▼             │
     mercatura_dev      │
        catalog         │
          │             │
          ▼             │
       landing          │
        schema          │
          │             │
          └──────┬──────┘
                 ▼
        source_files volume
```

Terraform is useful since it infers many dependencies since one resource references attributes from another.

For instance:

```hcl
azure_managed_identity {
  access_connector_id = azurerm_databricks_access_connector.unity_catalog.id
}
```

Connects the AzureRM resource directly to the Databricks resource

## Databricks Workspace Boundary

The development workspace (`dbw-mercatura-dev-uks`) is currently a Terraform data source rather than a Terrafrom managed Azure resource. So, Terrafrom does not own its lifecycle.

This is because the current AzureRM workspace resource in Terraform did not provide full coverage of the already estanlished workspace. Speciically, the workspace is serverless, and this platfrom property is not replicated by Terraform and the AzureRM provider as this time of implementation.

Since the current Terraform resources could only partially represent the development workspace, Terraform does not have ownership of it.

## Terraform State Architecture

Another important design decision was to keep the Terraform state stored outside of the Mercatura data plane.

```txt
rg-mercatura-tfstate-uks
    │
    └── dedicated StorageV2 account
            │
            └── tfstate
                  │
                  └── dev/azure.tfstate
```

The Terraform states are stored in a dedicated resource group, and in a dedicated storage account. This storage account is not ADLS Gen2 and hierarchical namespace (HNS) is disabled (unlike the mercatura data platform data plane). Instead, I am using ordinary Blob storage since:

- The Terraform states are a small object rather than any significant volume of data
- Blob versioning is very important for state recovery
- no data lake namespace is required

## Backend Protection

The remote back end is designed with several layers of protection:

- Microsoft Entra ID authentication for simple and robust enterprise oriented authorization that avoids distributing secrets and access tokens.
- container scoped Blob Data Contributor permissions so permissions are not distributed past the storage entities that are required 
- private tfstate container so the Terraform state files are more isolated
- Blob versioning to protect from an incorrect stat overwrite
- Blob soft delete to protect from deletion of the state container
- CanNotDelete Azure resource lock to protect the backend storage account from accidental deletion
- Azure Blob state locking to prevent simultaneous Terraform writers from corrupting or overwriting a shared state.

## Bootstrap Boundary

I first created the backend resources manually. This because Terraform can not create its own remote backend before It has somewhere to store its remote state. This is normal, since every IAC system has some sort of bootstrap boundary somewhere, hence why I am documenting it so its explicit.

## Identity Boundary

The identity lifecycle is kept seperate from the platform authorisation. I currently have established two account groups via Databricks workspace:

- `mercatura-dev-platform-admins`
- `mercatura-dev-data-engineers`

Terraform reads them, and does NOT create them. The architecture is as follows:

```txt
Databricks / organisational identity layer
        │
        ├── creates groups
        └── manages human membership
                │
                ▼
Terraform reads group identities
                │
                ▼
Unity Catalog authorization
```

I elected on this design after unsuccessful attempts to make Terraform own the account group lifecycle. The first attempt, there was an issue of the account-level provider authentication for my identity that could not be established. Then the workspace provier account group creation planned correctly, but failed with 404 error on apply.

Rather than spending lots of time finding workarounds, I just moved the identity lifecycle outside the Terraform platform state, which is fine since identity and account group permissions being typically is managed outside of cloud infrastructure at the system level.

## Unity Catalog Ownership

The platform administration group has ownersgip over the main development securables:

```txt
mercatura-dev-platform-admins
        │
        ├── mercatura_dev
        ├── mercatura_dev.landing
        ├── mercatura_dev.landing.source_files
        ├── mercatura_dev_storage
        ├── mercatura_dev_managed
        └── mercatura_dev_landing
```

Members of the administrative group inherits inherit broader authorities. I gave myself an administrator role. This is so when I no longer require ownership of the securables I can give myself least privilege access as a production security consideration. Furthermore, the establishment of groups helps avoid ownership of the entire platform architecture being tied to a singular identity, instead many members can inherit privileges when necessary.

## Data Engineer Privileges 

I created a data engineer group that receives only catalog usage, schema usage, and volume reading permissions.

```txt
mercatura-dev-data-engineers
    │
    ├── USE_CATALOG
    │     mercatura_dev
    │
    ├── USE_SCHEMA
    │     mercatura_dev.landing
    │
    └── READ_VOLUME
          mercatura_dev.landing.source_files
```

data engineers get no writing privileges, I am keeping roles distinct and explicity in the scope of thier permissions. The key segementation of roles I am establishing is:

```txt
source producer
    writes landing

data engineer
    reads landing

platform admin
    governs landing
```

## Terraform Source Layout

The current environment layout for the infrastructure is:

```txt
infrastructure/
└── terraform/
    └── environments/
        └── dev/
            ├── backend.tf
            ├── backend.hcl.example
            ├── locals.tf
            ├── main.tf
            ├── outputs.tf
            ├── providers.tf
            ├── unity_catalog.tf
            ├── unity_catalog_grants.tf
            ├── identity.tf
            ├── variables.tf
            ├── versions.tf
            └── .terraform.lock.hcl
```

I have not introduced any reusable modules at this point in development. Since there is only one real environment implementation (the development environment) at this point in time, module extraction would be premature. I will introduce modules when I start introducing multiple environments or have lots of repeated platform components that create genuine duplications.

## Configuration VS State VS Reality

I am using the following model:

```txt
HCL configuration
    desired state

Terraform state
    identity mapping + cached provider observations

Azure / Databricks
    actual infrastructure
```

The terraform planning serves to compare all three. The ideal circumstance is a terraform plan having zero infrastructural drift which directly indicates that the configuration matches the state, which also matches the infrastructure existing. 

Therefore, If in production, any manual changes a person makes with Azure or Databricks resources manually will be detected in the next plan as drift.

## Import Architecture

I imported the existing resources instead of recreating them. Key mappings include:

- `azurerm_storage_account.data` -> actual Azure storage account
- `databricks_catalog.dev` -> `mercatura_dev`

After the adoption was complete and verified, I removed the import configuration. So, now the normal resource blocks and remote state maintain ownership.

## CI Architecture

The initial Terraform CI layer is static and free of credentials. The GitHub Actions do:

- `terraform fmt -check`
- `terraform init -backend=false`
- `terraform validate`

Terraform plan and apply are not being run in the CI workflow since those operations require trusted access to Azure, Databricks, and the remote Terraform state. Future implementations of the CI/CD workflow will likely include full authentication ising OIDC / workload identity federation.

## Failure Domain Seperation

From everything mentioned in the documentation so far, the overall design of the project Meridian project, and the Mercatura data platform infrastructure architecture, the underlying design is to keep failure modes isolated in domains:

- Terraform backend is seperate from the Mercatura data storage
- Azure infrastructure is seperate from the Databricks infrastructure
- Identity lifecycle is seperate from the platform authorisation
- static CI is seperate from authenticated deployment

Keeping things seperate like this makes the blast radius issues more clear and makes future troubleshooting easier.

## Troubleshooting By Layer 

Here I am describing some potential troubleshooting patterns that arise and their clear origins due to the segementation of the failure domains.

#### Terraform cannot acquire state

Investigation should be focused on:

- backend authentication
- container RBAC
- Blob lease / state lock
- notework access
- backend configuration 

#### Azure resource refresh fails

Investigate:

- Azure CLI login
- subscription context
- Azure RBAC
- AzureRM provider configuration 

#### Databricks resource refresh fails

Investigate:

- mercatura-dev profile
- workspace identity
- Unity Catalog privileges
- group membership
- object ownership 

#### Terraform Validate fails in CI

Investigate:

- HCL
- provider schema
- broken references
- lock file
- provider installation 
