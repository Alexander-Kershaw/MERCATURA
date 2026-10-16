# ADR-0003: Infrastructure As Code (IAC) Strategy

- Status: Accepted
- Data: 2026-10-14
- Scope: Terraform, Azure infrastructure, Databricks and Unity Catalog infrastructure, Terraform states, identity boundaries, CI validation

## Contex

I had initially bootstrapped the development environment for the mercatura data platform manually via the Azure CLI, Databricks CLI, and with Databricks SQL. This set up the core foundation of the core infrastructure of my intended platform. It was also beneficial for understanding the Azure and Databricks resource model, especially before introducing any infrastructure as code. 

At this point, the mercatura platform development environment already contained the following after the initial bootstrapping:

- The Azure resource group: `rg-mercatura-dev-uks`
- Azure Databricks workspace: `dbw-mercatura-dev-uks`
- ADLS Gen2 storage account with managed and landing containers
- Databricks access connector: `ac-mercatura-dev-uks`
- managed identity storage access through Azure RBAC
- Unity Catalog storage credential: `mercatura_dev_storage`
- Unity Catalog external locations: `mercatura_dev_managed` and `mercatura_dev_landing`
- Unity Catalog catalog: `mercatura_dev`
- An external volume: `mercatura_dev.landing.source_files`

With this foundation established. I wanted to make the infrastructure foundational reproducible with IAC, making it more reviewable and safe to evolve over time.

I did not introduce IAC such as Terraform too early and risk recreating resources, encoding permissions I wasnt sure of, coupling the Terraform state to the resources Terraform itself manages, and overextending Terraform into identity lifecycle management that belongs elsewhere.

## Decision 

Terraform is used for the IAC tool to establish a more durable Azure and Databricks platform infrastructure. The implementation of Terraform is done after there is a clear picture of the infrastructure.

Therefore, the overall flow is as follows:

- Understand the manually provisioned infrastructure that was accomplished with Azure CLI thoroughly
- Describe the desired infrastructure (desired Terraform state) as the infrastructure target
- Import the existing resources into Terraform
- Verify that there is zero drift between plans
- Make the required changes to reach the desired infrastructure state
- Use a remote Terraform state
- Enforce quality gates

## Terraform Scope

Terraform has management over the following Azure resources:

- development resource group
- ADLS Gen2 storage account
- managed container
- landing container
- Databricks access connector
- Azure RBAC assignment for the Unity Catalog storage access

Terraform also manages the following Databricks and Unity Catalog resources:

- storage credentials
- external locations
- development catalog
- landing schema
- source files external volume
- unity catalog ownership
- least privilege unity catalog grants

#### Resources Outside of the Terraform Lifecycle Ownership

The existing serverless Azure Databricks workspace is read through an AzureRM data source instead of being managed as an AzureRM resource. This is because at this time of implementation the AzureRM workspace resource did not failthfully model the exiting workspaces serverless `compute_mode` property.

Therefore, I did not force this resource into Terraform and give it management of the lifecycle ownership since I want the provider to be able to accurately represent all parts of the existing workspace configuration is it is.

Hence, the workspace is treated as an external platform dependency.

#### Terraform Backend Bootstrap Resources

The dedicated Terraform state resource group and storage account was manually bootstrapped. This resource group and storage account exist so Terraform can function and form the bootstrap boundary beneath the Terraform managed platform stack. This is intended to avoid circular dependency issues such as Terraform requiring state storage in order to create the storage that contains that exact same state.

#### Human and Account Identity 

Terraform does not curently create or manage any of the mercatura data platform Databricks account groups. There are two groups created through the Databricks identity management path (done in Databricks workspace itself). These groups are:

- `mercatura-dev-platform-admins`
- `mercatura-dev-data-engineers`

Terraform reads these groups as data sources and uses them when assigning the Unity Catalog ownership and priviliges.

This was a work around an error I encountered after attempting to use Terraform to create the account groups using `api="account"`. This approach planned successfully but failed to apply with HTTP 404 not found error.

So, I established the groups within the workspace. Therefore, the identity lifecycle is treated as an external dependency. This is okay practice since within enterprise, identities are typically sourced from an organisation;s identity management system rather than being created by a data platform Terraform stack, so this is no issue.

## Existing Resource Adoption

Using Terraform import, the existing infrastructure existing as the mercatura data platform are adopted, rather then deleting and recreating them.

For the Azure resources, the import produced the expected infrastructure with no drift. However, for the Unity catalog resources, the initial plan exposed some drift. But this drift was minor due to differences in the comments associated with resources. I adjusted the differences so both the established infrastructure, and the Terraform plan matched, resulting in a plan with no drift.

Therefore, the configuration faithfully matches the established infrastructure since the plans for the resources ceased drifting.


## Remote State

The Terraform state is stored remotely in a dedicated Azure Blob Storage account. The backend is isolated from the Mercatura data-plan storage account.

The backend design includes:

- dedicated resource group
- dedicated StorageV2 account
- HNS disabled
- private `tfstate` container
- Microsoft Entra ID authentication
- container scoped `Storage Blob Data Contributor` permissions for myself
- Blob versioning
- Blob soft delete 
- container soft delete
- `CanNotDelete` Azure resource lock
- Azure Blob native state locking

The development state key is `dev/azure.tfstate`

The backend account is not the same storage account that is being managed by Terraform for the Mercatura data platform.

## Authentication

Authentication is done via the Azure CLI with `az login`. Terraform's AzureRM provider uses the Azure CLI authenticated context.

For databricks, authentication for the workspace is done using a OAuth profile `mercatura_dev`. The Databricks Terraform provider reuses this profile. Therefore, no Databricks PAT, storage account key, or any long-lived client secrets are required to access the normal workflows.

## CI Authentication

The initial CI workflow is intentionally free of access credential requirements and performs static validation only. Later, the authenticated CI/CD will use workload identity federation / OIDC rather than using credentials or long-lived secrets.

## Ownership Model

Unity Catalog objects are owned by `mercatura-dev-platform-admins` rather than any individual in particular. I am currently within the platform admin group which gives my authority via memvership rather than personal ownership. The platform admin permissions are broad and will allow for development to continue relatively uninhibited.

## Least Privilege Data Engineer Group

I have created another group `mercatura-dev-data-engineers` which receives privileges scoped just to the current landing architecture. This group can use catalogs, schemas, and read volumes. This group does not have privileges to manage resources, write volumes, or direct privileges themselves. The landing area is source level data and should not be mutated, hence why it only has read only privileges attached to data engineers. 

## Grant Management

I am using principal-specific Terraform grant resources instead of making complete privilege sets authoritative in a singel resource to avoid accidentally deleting privileges managed by another administrative process.

## Destruction Protection

The most significant resources have lifecycle protections. For instance, the development ADLS account and important Unity Catalog securables are protected from accidental Terraform destruction. Note, that this doesn't make these resources completely immutable and impossible to delete, but ensures that destructive operations cannot go ahead and require explicit architectural decisions.

## Provider Versioning

I have contrained the provider version requirements in configuration. The exact provider verions are committed via `.terraform.lock.hcl`.

This lock file is generated for:

- macOS Apple Silicon
- macOS x86-64
- Linux x86-64

Therefore, both my local macOS development environment is support as well as the GitHub Linux CI.

## Static Validation

I am using a static Terraform validation script that is free from credentials.

The script follows this general structure:

- checks canonical formatting
- copies Terraform configuration into an isolated temporary directory
- initialises the providers with `backend=false`
- uses the committed lock file in read only mode
- runs `terraform validate`

This prevents the static CI from contacting Azure, Databricks, or the remote Terraform state backend.

## CI

GitHub Actions runs the Terraform static checks on any relevant pull requests and pushes. This initial workflow does not run an authenticated Terrafrom plan. Later, a more complete plan will be implemented that includes Azure access, Databricks access, and the remote state access. This will be introduced after a dedicated CI workload identity exists.

## Alternatives Considered

#### Recreate Infrastructure With Terrafrom

I rejected this approach. The working infrastructure provisioned via the Azure CLI during bootstrapping was already manually verified. Recreating the infrastructure would just introduce needless risk and destroy learning opportunities in resource adoption, since I have already had experience creating infrastructure directly from terraform, learning about resource adoption was more valuable to me.

#### Keep Local Terraform State

Rejected.

Since I am targeting this project as more production level, I want to emulate production conditions, with ultimately involves collaborative environments. Keeping the Terraform stat local would make it difficult to collaborate with other developers, furthermore, local state lack shared locking.

Local terraform states was used as much as it had value, before migrating it to Azure Blob Storage.

#### Storing Terrafrom State in the Mercatura Data Lake

Rejected.

This would be a circular dependency issue. This approach would couple the Terrafrom recovery mechanism to a stateful resource managed by the same configuration.

#### Using storage account keys for backend authentication

Rejected.

I am using Microsoft Entra identity and Azure RBAC instead of using storage account keys. 

## Consequences

#### Benefits

- Azure and Unity Catalog infrastructure is reproducible
- Terrafrom state is remote and locked
- state recovery protection exists
- cloud authentication avoids long-lived storage keys and Databricks PATs
- Ownership is based on group membership
- engineering access follows least privilege principles
- CI can catch formatting and provider schema errors without the need of cloud credentials
- provider versions are reproducible across different developer and CI platforms

#### Negatives

- Databricks workspace remains outside of Terrafrom lifecycle management
- account group creation is currentlyy manual and owned by the identity system
- future CI/CD requires a seperate workload identity 

