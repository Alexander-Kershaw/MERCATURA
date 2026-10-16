# Devlog 0004 - Terraform Foundation 

- Data range: 2026-10-11 to 2026-10-14

## Objective

Introduce Terraform after the Azure and Unity Catalog architecture was manually built.

Requirements included:

- safe adoption of existing Azure resources
- remote state and state locking
- safe adoption of Unity Catalog resources
- group based ownership
- least privilage Unity Catalog grants
- provider and backend reproducibility 
- static CI free from credentials
- zero drift detection in Terraform plans

---

## Starting State

I already had established a working development environment before introducing terraform at this stage. I had provisioned both Azure and Unity Catalog resources via CLI.

For Azure:

```
rg-mercatura-dev-uks
dbw-mercatura-dev-uks
ADLS Gen2 storage account
managed container
landing container
ac-mercatura-dev-uks
Storage Blob Data Contributor assignment
```


and for Unity Catalog:

```txt
mercatura_dev_storage
mercatura_dev_managed
mercatura_dev_landing
mercatura_dev
mercatura_dev.landing
mercatura_dev.landing.source_files
```

Since all these resources were created manually, I understood the reponsibilities of each before moving to automation with terraform.

---

## Terraform Repository Structure

I created a dedicated repository for all Terraform related works: `infrastructure/terraform/environments/dev/`. Each .tf file handles a specific concern, resulting in the following files being present in the directory:

```txt
versions.tf
providers.tf
variables.tf
locals.tf
main.tf
outputs.tf
backend.tf
unity_catalog.tf
identity.tf
unity_catalog_grants.tf
```

--- 

## Azure Provider Configuration

I added the AzureRM provider in Terraform. The Azure authentication used the existing Azure CLI session I was logged into. The provider was configured for Microsoft Entra storage authentication rathen than using a Shared Key access approach. This was in alignment with the ADLS account configuration, where the Shared Key authentication setting had already been disabled.

---

## Databricks Workspace Provider

The existing serverless Azure Databricks workspace was not imported as an AzureRM managed resource.

This was because the current provider model does not expose the serverless workspace compute mode configuration. Therefore, instead of using AzureRM for provisioning the Databricks Workspace, I am reading the existing workspace with `data.azurerm_databricks_workspace.dev`.

This is a workaround the limitation of the current Databricks provider not having full coverage of the existing workspace that was already created. I did not want to claim that Terraform could completly manage the resource if it could not accurately describe what was already existing.

---

## Azure Resource Adoption

I wrote the Terraform configuration to describe the following existing resources: 

```txt
resource group
storage account
managed container
landing container
Access Connector
Storage Blob Data Contributor assignment
```

Configuration driven importation was used to create the initial resource adoption plan. This resulted in the following plan summary:

```txt
6 to import
0 to add
0 to change
0 to destroy
```

This was the result I was expected and was ideal since no resources were added, changed, or destroyed, indicating a zero-drift plan which encapsulated the existing Azure infrastructure faithfully.

I applied the plan and no changes were reported after a subsequent terraform plan execution, solidifying that no infrastructural drift was occuring. The imporary import configuration file was then removed since it served no more apparent value.

---

## First Terraform Management Mutation

After the success of the initial adoption plan and application, I changed the tags on resources to represent the new state mutation. Since Terraform managed the resources after the application, the CLI ownership of resource management was now void, hence the change in tags. For example:

`managed_by = cli` was mutated into `managed_by = terraform`

This was the first demonstration of a full Terraform lifecycle:

- Describing the resources / desired infrastructure
- Importing existing infrastructure
- Verifying that infrastructure
- Changing the desired Terraform state (such as changing the resource tags in this circumstance)
- Applying the Terraform plan
- Applying the plan if there are no issues
- Verifying the infrastructure again with a subsequent plan execution and inspecting resources directly in the Azure interface 

---

## Remote State Design

Initially, I used a local terraform state for the initial resource adoption work. For a more production ready system, I decided to create a seperate remote backend for containing Terraform states, which is beneficial for infrastructural recovery in the event of an error.

The seperate backend was created as such: 

```txt
rg-mercatura-tfstate-uks
    ↓
dedicated StorageV2 account
    ↓
tfstate container
    ↓
dev/azure.tfstate
```

Notice, that the remote backend is not located in the actual Mercatura data platform ADLS account. Instead, it has its own resource group and storage account to house terrafor states in a dedicated container.

This avoids coupling the Terraform state recovery mechanism to data-plane infrastructure that was managed by the same Terraform configuration.

---

## Backend Security and Recovery

The remote backend was configured with:

- Microsoft Entra authentication
- Shared Key access disabled
- Private container
- container scoped Blob Data Contributor
- Blob versioning
- Blob soft delete
- container soft delete
- CanNotDelete sotrage account locking

---

## State Migrations

The Terraform backend configuration used the following:

```txt
azurerm backend
use_cli = true
use_azuread_auth = true
```

Specific environment backend coordinates were stored outside of Git in `backend.hcl`. An example `backend.hcl.example` was committed instead. 

The state was migrated using the following command:

```bash
terraform init -migrate-state -backend-config=backend.hcl
```

Then I verified the state with: 

```bash
terraform state list
terraform plan
```

Upon inspection, within the private container in the dedicated terraform state resource group, I found `dev/azure.tfstate` as expected. This confirmed successful migration from local state to remote backend state.

---

## Databricks Provider 

I added the Databricks Terraform provider, using local authentication that reused the existing `mercatura-dev` OAuth profile. I did not introduce any Databricks PATs (personal access tokens) or client secrets. At this state, both Azure and Databricks participated in one Terraform dependency graph. 

An example of such a dependency is as follows: the Unity Catalog storage credential references the Azure Acess Connector resource that is managed by AzureRM provider, hence the interdependency of Azure and Databricks in one configuration.

---

## Unity Catalog Adoption

The existing Unity Catalog resources were written in the Terraform configuration as a resource adoption plan. The configuration covered all existing Unity Catalog resources:

```txt
mercatura_dev_storage
mercatura_dev_managed
mercatura_dev_landing
mercatura_dev
mercatura_dev.landing
mercatura_dev.landing.source_files
```

The initial adoption plan execution indicated 6 imports and 6 changes, with 0 additions and 0 resourse destruction.

```txt
6 to import
0 to add
6 to change
0 to destroy
```

This initial drift in infrastructure was due to superficial changes in comments associated with the resources. After correcting the comments such that the Terraform configuration matched the preestablished resource, I applied the plan again.

This plan became:

```txt
6 to import
0 to add
0 to change
0 to destroy
```

This plan indicated no drift and represented the desired resource adoption state. Therefore, I executed Terraform apply and imported the resources successfully.

--- 

## Identity Architecture - Initial Attempt

I encountered some issues with establishing the desired identity design.

I had the intention of creating two Databricks account groups with Terraform managing them. These groups were:

```txt
mercatura-dev-platform-admins
mercatura-dev-data-engineers
```

I initially considered an account-level provider. However, I could no access the Databricks account console since this involved authentication in my browser that returned an error involving `tenant 'Microsoft Services'` and the Azure Databricks application ID.

An identity I previously assumed to be the Databricks account ID was later discovered in SCIM output to be my external ID.

Ultimately, I abandoned this approach as I did not want to guess further account-level configuration.

---

## Identity Architecture - Workspace Provider account group attempt

I attempted establishing the Databricks identity groups using the workspace provider with the `api="account"` setting on the Databricks group resources.

Upon executing the Terraform plan with this change implemented, Terraform successfully returned:

```txt
6 to add
0 to change
0 to destroy
```

for two groups, two group memberships, and two workspace assignments. However, the Terraform apply failed with: 

```txt
Error: cannot create group: Not Found
```

For both account groups. Therefore, No group resources were created. I abandoned this approach too.

---

## Final Identity Boundary

I finally elected to create the account groups via the Databricks workspace identity management interface. I created both `mercatura-dev-platform-admins` and  `mercatura-dev-data-engineers` and added myself to both groups. 

Instead of Terraform managing the account group lifecycles, Terraform instead reads them as data sources as part of this workaround. 

This, as a result created a cleary identity boundary:

- The identity layer create groups and memberships (done within the databricks workspace in the identity management interface)
- Terraform consumes the group identities but does not manage them
- Unity Catalog recieves ownerships and grants

This actually ended up being closer to realistic enterprise identity design where identity is typically owned by the system identifyer framework (Entra ID / IAM) rather than owned by the data platform in itself. 

---

## Unity Catalog Access Regression and Recovery

After completing the identity transition, Terraform refresh failed with the following messages:

```txt
cannot read storage credential:
User does not have any privileges on Credential 'mercatura_dev_storage'

cannot read catalog:
User does not have USE CATALOG on Catalog 'mercatura_dev'
```

Both the Azure and Terraform state were healthy. So, the failure was isolated to Databricks authorisation.

To address this I manually transfered the catalog and storage credential ownership to the platform administrator group `mercatura-dev-platform-admins` which I was already a member of.

After that change both:

```bash
databricks catalogs get mercatura_dev --profile mercatura-dev
databricks storage-credentials get mercatura_dev_storage --profile mercatura-dev
```

were successfully executed. This is just an issue to read privileges.

---

## Remaining Ownership Transition

I implemented some remaining ownership changes with Terraform encompassing:

```txt
mercatura_dev_managed
mercatura_dev_landing
mercatura_dev.landing
mercatura_dev.landing.source_files
```

The ownership was transfered from my personal user to the `mercatura-dev-platform-admins` group which I am part of anyway.

With the application of the plan, I had the following returned:

```txt
3 to add
4 to change
0 to destroy
```

These changes covered applying least privilege data engineer group grants. no resources were replaced.

---

## Data Engineer Privileges

The Terraform created data engineer group grants as as follows:

```txt
mercatura_dev
    USE_CATALOG

mercatura_dev.landing
    USE_SCHEMA

mercatura_dev.landing.source_files
    READ_VOLUME
```

I intentionally gave the data engineer groups no writing priveleges. No privileges were granted directly on storage credentials or external locations. Therefore, the infrastructure-level storage objects are intentionally being kept seperate from ordinary data engineering access.

---

## Provider Lock 

I prepared a Terraform dependency lock file to support macOS development and the Linux CI. 

```txt
darwin_arm64
darwin_amd64
linux_amd64
```

---

## Static Validation Script

I created a CI static validation script `scripts/check-terraform-static.sh`. 

The script does the following:

- Checks the Terraform formatting
- creates an isolated temporary Terraform directory
- copies HCL and dependecy lock file
- runs `terraform init -backend=false - lockfile=readonly`
- runs `terraform validate`
- removes the temporary directory

Therefore this static checks do no rely on Azure credentials, Databricks credentials, or access to the remote backend terraform state.

---

## GitHub Actions CI

I created `.github/workflows/terraform-static.yml`.

This workflow runs the static Terraform validation for relevant changes to the repository. This does not run an authenticated plan and this is deliberate. A future authenticated workflow will be implemented and uses a dedicated workload identity rather than using my person Azure or Databricks session.

The Terraform static CI passed, and I authenticated the workflow locally too, which also passed.

---

## Current State

The current state of project Meridian includes the following milestones:

- Azure Mercatura data platform infrastructure is represented in Terraform
- Unity Catalog infrastructure is represented in Terraform
- The project can compose Azure and Databricks dependencies accross providers
- The Terraform state can be stored remotely 
- Previous state versions can be recovered
- States are locked
- Infrastructure drift is detectable
- Unity Catalog has group based ownership assignment
- Unity Catalog grants are managed with least-privilege principles
- The Terraform state can be validated without cloud credentials
- Terraform static checks are enforced in CI

Terraform does not currently own:

- The Azure Databricks workspace lifecycle
- THe Terraform backend bootstrap infrastructure
- Databricks account group lifecycle
- Human identity lifecycle

---

## Lessons 

- Importation and resource adoption is significant. The configuration must be reconciles with the reality of the existing infrastructure architecture first.
- Clean adoption plans are valuable evidence, and give confidence that an adoption will not mutate the environment.
- Provider support should contrain ownership. Terraform should not own a resource that it can not faithfully represent in configuration.
- States are operationally significant, they should be isolated, recoverable, and locked.
- IaC does not have to own identity lifecycles. Instead, it may be cleaner for a data platform to consume organisational groups rather than create and manage them.
- Group ownership is stronger than having personal ownership.
- CI should gain privileges only when its required. Static validation is useful as it does not require cloud credentials. The authenticated CI will have to wait until a proper workload identiy exists.



