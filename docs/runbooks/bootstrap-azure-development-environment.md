# Project Meridian — Azure Development Environment Bootstrap Runbook

## Purpose

This runbook documents the manual bootstrap of the Project Meridian Azure development environment.

It records:

- the Azure CLI commands used
- the Databricks CLI commands used
- what each command does
- which platform or control plane the command interacts with
- why the command was required
- what should be verified after each step
- which parts are temporary bootstrap operations rather than the intended long-term architecture.

I wanted to document the Azure and Databricks CLI commands used so someone else can reproduce the exact workload faithfully exactly how I did it at the current development stage.

The objective is to understand the Azure and Databricks resource model before automating it.

---

# 1. Control planes and command-line tools

Two different command line tools are used during the bootstrap.

## Azure CLI

Command:

```text
az
```

Azure CLI communicates primarily with Azure Resource Manager and Azure service APIs.

It is used for resources such as:


- resource groups
- Azure Databricks workspaces
- storage accounts
- Databricks Access Connectors
- managed identities
- Azure RBAC
- storage containers

Examples:

```bash
az group create
az storage account create
az databricks access-connector create
az role assignment create
```

Note that a very useful Azure CLI extention is:

```bash
az interactive
```

This provides an interactive terminal window that shows the CLI commands and has autocorrect capabilities. This is much better then needing to refer to docs constantly for correct CLI commands, you can infer quite easily with this extention.

## Databricks CLI

Command:

```text
databricks
```

Databricks CLI communicates with the Databricks control plane and workspace APIs.

It manages objects such as:


- Unity Catalog storage credentials
- external locations
- catalogs
- jobs
- pipelines
- workspace files
- bundles

Examples:

```bash
databricks catalogs list
databricks storage-credentials create
databricks external-locations create
```

The Azure CLI and the Databricks CLI are responsible for different things, Azure being infrastructure related, and Databricks being data platform related.

```text
Azure CLI
    ↓
Azure infrastructure

Databricks CLI
    ↓
Databricks platform
```

A Databricks storage credential cannot grant Azure permissions.

An Azure RBAC assignment cannot grant a user permission to a Unity Catalog table.

Both layers must be configured correctly in order to establish functional access paths bridging Azure resources and Databricks.

---

# 2. Verify local tooling

## Azure CLI

```bash
az version
```

### What it does

Displays the installed Azure CLI version and installed extensions.

### Why

I am using Azure CLI to create and inspect Azure resources.

If Azure CLI is unavailable, I install it on macOS with brew:

```bash
brew install azure-cli
```

---

## Databricks CLI

```bash
databricks -v
```

### What it does

Displays the installed Databricks CLI version.

### Project Meridian result

The environment used:

```text
Databricks CLI v1.19.0
```

### Why

The Databricks CLI will later be used for:

- authentication
- Unity Catalog
- Declarative Automation Bundles
- jobs
- pipelines
- deployments


---

# 3. Authenticate to Azure

```bash
az login
```

## What it does

Starts an interactive Microsoft Entra authentication flow.

After authentication, Azure CLI receives tokens that allow commands to operate as the signed-in user.

## Why

Azure must know which identity is requesting resource creation and management. Many Microsoft Entra IDs exists, different users with different permissions.

This authentication does not mean that the user automatically has permission to every Azure resource.

Permissions are still controlled through Azure RBAC.

---

# 4. Inspect available subscriptions

```bash
az account list \
  --query "[].{name:name,id:id,state:state,isDefault:isDefault}" \
  --output table
```

## What it does

Lists Azure subscriptions visible to the authenticated identity.

The `--query` argument uses JMESPath to return only selected properties.

The `--output table` argument formats the result for humans. You can choose different output formats but the table formast is most legible.

## Why

A user can belong to multiple Azure subscriptions of different tiers.

Before creating resources, I needed to know which subscription Project Meridian will use.

I am using my default subscription which enables me broad access to the Azure services since I am paying as I go, rather than using a free trial.

---

# 5. Inspect the active subscription

```bash
az account show \
  --query "{name:name,id:id,tenantId:tenantId,state:state}" \
  --output table
```

## What it does

Shows the subscription currently selected by Azure CLI.

## Why

Azure commands execute against a current subscription context.

Creating resources in the wrong subscription is an easy and potentially expensive mistake. 

---

# 6. Select the Project Meridian subscription

If multiple subscriptions exist:

```bash
az account set --subscription "<SUBSCRIPTION-NAME>"
```

## What it does

Changes the active Azure CLI subscription context.

## Why

All subsequent Azure resources needed to be created inside the intended Project Meridian subscription.

## Security note

Subscription IDs and tenant IDs are not passwords, but Project Meridian documentation does not need to record them. These IDs are not to be committed to the repository.

---

# 7. Install the Azure Databricks CLI extension

```bash
az extension add --name databricks
```

## What it does

Adds the Azure CLI extension that exposes Azure Databricks resource-management commands.

Examples include:

```bash
az databricks workspace
az databricks access-connector
```

## Why

The ordinary Azure CLI does not contain all the Databricks Azure resource commands directly.

The extension manages the Azure Resource Manager side of Databricks.

This is separate from the standalone databricks CLI that encompasses the platform functionality and operations rather than the underlying related Azure infrastructure and connections.

---

# 8. Verify the Azure Databricks extension

```bash
az databricks workspace --help
```

## What it does

Displays supported Azure Databricks workspace operations.

## Why

This verifies that the extension is available before attempting workspace creation.

---

# 9. Create the development resource group

```bash
az group create \
  --name rg-mercatura-dev-uks \
  --location uksouth \
  --tags \
    project=meridian \
    organisation=mercatura \
    environment=dev \
    managed_by=cli \
    purpose=data-platform
```

## What is an Azure resource group?

A resource group is a logical container for collections of Azure resources.

Project Meridian currently groups the development infrastructure under:

```text
rg-mercatura-dev-uks
```

The naming convention means:

```text
rg          resource group
mercatura   organisation/system
dev         environment
uks         UK South region
```

## What the command does

Creates the resource group in UK South and applies appropriate metadata tags.

## Why tags matter

Tags provide searchable metadata for:

```text
cost analysis
ownership
automation
resource discovery
governance
```

They do not change the technical behaviour of the resource. Tagging is useful in many ways, especially since I want to control the budget for this project.

## Verification

```bash
az group show \
  --name rg-mercatura-dev-uks \
  --query "{name:name,location:location,provisioningState:properties.provisioningState,tags:tags}" \
  --output json
```

Expected:

```text
provisioningState = Succeeded
```

This just means that the resource group now exists.

---

# 10. Create the Azure Databricks workspace

```bash
az databricks workspace create \
  --resource-group rg-mercatura-dev-uks \
  --name dbw-mercatura-dev-uks \
  --location uksouth \
  --sku premium \
  --compute-mode Serverless \
  --tags \
    project=meridian \
    organisation=mercatura \
    environment=dev \
    managed_by=cli \
    purpose=data-platform
```

## What it creates

An Azure Databricks workspace resource.

The development workspace is:

```text
dbw-mercatura-dev-uks
```

## Why Premium

Project Meridian requires enterprise capabilities including Unity Catalog and production style governance. Furthermore, premium is now the only option according to modern documentation. 

## Why Serverless

For the development environment I wanted:


- low operational overhead
- no permanently running clusters
- reduced infrastructure management
- fast experimentation

The production-reference architecture will later examine a more explicitly controlled network topology. But for the development environment, this is more than sufficient and should be relatively inexpensive with autotermination enabled on clusters and SQL warehouse compute.

## Verification

Wait for provisioning:

```bash
az databricks workspace wait \
  --resource-group rg-mercatura-dev-uks \
  --name dbw-mercatura-dev-uks \
  --created
```

Then inspect:

```bash
az databricks workspace show \
  --resource-group rg-mercatura-dev-uks \
  --name dbw-mercatura-dev-uks \
  --query '{
    name:name,
    location:location,
    sku:sku.name,
    provisioningState:provisioningState,
    workspaceUrl:workspaceUrl,
    computeMode:computeMode
  }' \
  --output json
```

Expected important properties:

```text
Premium
Succeeded
Serverless
```

This is just my way of verifying that the databricks version is premium, and that the workspace is successfully created and will use serverless compute.

---

# 11. Retrieve the Databricks workspace host

```bash
az databricks workspace show \
  --resource-group rg-mercatura-dev-uks \
  --name dbw-mercatura-dev-uks \
  --query workspaceUrl \
  --output tsv
```

## What it does

Returns the Databricks workspace hostname without additional JSON formatting.

Example shape:

```text
adb-....azuredatabricks.net
```

## Why

The standalone Databricks CLI needs the Databricks workspace host for authentication.

---

# 12. Store the workspace host in the shell

```bash
export DATABRICKS_HOST="https://$(az databricks workspace show \
  --resource-group rg-mercatura-dev-uks \
  --name dbw-mercatura-dev-uks \
  --query workspaceUrl \
  --output tsv)"
```

## What it does

Executes the Azure CLI query and stores the resulting URL in the shell variable:

```text
DATABRICKS_HOST
```

## Why

This avoids repeatedly copying and pasting the workspace hostname which would be incredibly tedious.

## Important

`export` affects only the current shell session unless it is added to shell configuration.

---

# 13. Authenticate the Databricks CLI

```bash
databricks auth login \
  --host "$DATABRICKS_HOST" \
  --profile mercatura-dev
```

## What it does

Starts an OAuth login flow against the Databricks workspace.

The resulting Databricks authentication configuration is stored under the profile:

```text
mercatura-dev
```

## Why OAuth instead of a PAT

OAuth avoids immediately introducing a long-lived personal access token.

The profile gives us a stable local name for the development environment.

Future commands can therefore use:

```bash
--profile mercatura-dev
```

---

# 14. Verify Databricks authentication

```bash
databricks auth profiles
```

and:

```bash
databricks current-user me \
  --profile mercatura-dev
```

## What these prove

The first command shows available authentication profiles.

The second verifies that the profile can make an authenticated Databricks API call.

---

# 15. Initial workspace discovery

```bash
databricks catalogs list \
  --profile mercatura-dev
```

```bash
databricks warehouses list \
  --profile mercatura-dev
```

```bash
databricks workspace list / \
  --profile mercatura-dev
```

## Why discovery before configuration

Before designing infrastructure around assumptions, I inspect what the newly provisioned workspace actually contains.

---

# 16. Generate a globally unique storage-account name

```bash
export MERIDIAN_SUFFIX="$(openssl rand -hex 3)"
export STORAGE_ACCOUNT="stmercaturadev${MERIDIAN_SUFFIX}"

echo "$STORAGE_ACCOUNT"
```

## Why a suffix is required

Azure Storage account names are globally unique across Azure.

A deterministic name such as:

```text
stmercaturadev
```

is therefore likely to already exist.

`openssl rand -hex 3` produces three random bytes represented as six hexadecimal characters. This allowed me to make globally unique names.

## Important

This random suffix was for bootstrap convenience.

Terraform will later include a deterministic naming strategy that can still satisfy Azure global uniqueness constraints.

---

# 17. Create the ADLS Gen2 account

```bash
az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group rg-mercatura-dev-uks \
  --location uksouth \
  --sku Standard_LRS \
  --kind StorageV2 \
  --enable-hierarchical-namespace true \
  --min-tls-version TLS1_2 \
  --https-only true \
  --allow-blob-public-access false \
  --allow-shared-key-access false \
  --public-network-access Enabled \
  --tags \
    project=meridian \
    organisation=mercatura \
    environment=dev \
    managed_by=cli \
    purpose=data-platform
```

## Important arguments

### `--sku Standard_LRS`

Uses locally redundant standard storage. For the development environment this provides an inexpensive storage tier.

### `--kind StorageV2`

Creates a general purpose Azure Storage v2 account.

### `--enable-hierarchical-namespace true`

This is the defining configuration that enables Azure Data Lake Storage Gen2 behaviour.

Without hierarchical namespace, the account is ordinary blob storage rather than the ADLS Gen2 architecture Project Meridian intends to use.

### `--min-tls-version TLS1_2`

Rejects older TLS versions.

### `--https-only true`

Requires encrypted network transport.

### `--allow-blob-public-access false`

Prevents anonymous public blob access.

### `--allow-shared-key-access false`

Disables authentication using account keys.

Project Meridian prefers:

Microsoft Entra identity + Azure RBAC

### `--public-network-access Enabled`

Allows access through the public Azure storage endpoint.

This is intentional for the development environment.

Private endpoints and restrictive networking are deferred to the production-reference architecture once the project is well underway.

---

# 18. Verify the storage account

```bash
az storage account show \
  --name "$STORAGE_ACCOUNT" \
  --resource-group rg-mercatura-dev-uks \
  --query '{
    name:name,
    location:location,
    kind:kind,
    sku:sku.name,
    hierarchicalNamespace:isHnsEnabled,
    minimumTls:minimumTlsVersion,
    publicNetworkAccess:publicNetworkAccess,
    sharedKey:allowSharedKeyAccess,
    blobPublicAccess:allowBlobPublicAccess
  }' \
  --output json
```

## Why

Provisioning succeeding does not inherently prove that the resource was configured as intended.

I inspected the important security and data-lake properties explicitly yo verify the configuration against expectations.

---

# 19. Retrieve the signed-in user's Entra object ID

```bash
export CURRENT_USER_OBJECT_ID="$(az ad signed-in-user show --query id -o tsv)"
```

## What it represents

This is the Microsoft Entra object identifier for the currently authenticated human user (the user being me / or you if you are following along).

## Why

Azure RBAC role assignments target identities using identifiers such as this object ID.

This value should not be confused with:

- subscription ID
- tenant ID
- client ID
- managed-identity principal ID

They represent different objects.

---

# 20. Retrieve the storage-account resource ID

```bash
export STORAGE_ID="$(az storage account show \
  --name "$STORAGE_ACCOUNT" \
  --resource-group rg-mercatura-dev-uks \
  --query id \
  -o tsv)"
```

## What it returns

An Azure Resource Manager ID representing the storage account.

Conceptual shape:

```text
/subscriptions/.../
resourceGroups/rg-mercatura-dev-uks/
providers/Microsoft.Storage/
storageAccounts/...
```

## Why

Azure RBAC assignments require a scope.

Using the resource ID scopes the permission to this storage account.

---

# 21. Temporarily granting storage data access

```bash
az role assignment create \
  --assignee-object-id "$CURRENT_USER_OBJECT_ID" \
  --assignee-principal-type User \
  --role "Storage Blob Data Contributor" \
  --scope "$STORAGE_ID"
```

## Why this was required

Creating the storage account is a management-plane operation.

Creating containers inside the account is a storage data-plane operation.

Having permission to manage the Azure resource does not necessarily mean the identity has permission to manipulate its contents.

This temporary role allowed the me to create the two containers using Entra authentication. Temporarily giving myself the data-plane permissions necessary on top of my core management-plane authorities.

## Why temporary

The normal Project Meridian architecture should not rely on developers accessing the physical storage directly. Consider under conventional development environment, multiple developers work in parallel, so data-plane permissions are not automatically given out to avoid accidental alteration of data that already may exist in storage.

---

# 22. Create the `managed` container

```bash
az storage container create \
  --name managed \
  --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login
```

## What it does

Creates an ADLS container using the currently authenticated Entra identity.

## Why `--auth-mode login`

It tells Azure CLI to authenticate using the Entra identity that I am currently signed in as, rather than an account key.

This is important because shared-key access was disabled.

## Responsibility

The `managed` container is reserved for Unity Catalog-managed platform data.

---

# 23. Create the `landing` container

```bash
az storage container create \
  --name landing \
  --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login
```

## Responsibility

The landing container will contain externally produced source files.

Examples include:

- supplier files
- source extracts
- legacy feeds
- simulator output
- acquisition files

It is not equivalent to Bronze, landing is the source level data.

---

# 24. Verify storage containers

```bash
az storage container list \
  --account-name "$STORAGE_ACCOUNT" \
  --auth-mode login \
  --query "[].name" \
  --output table
```

Expected:

```text
landing
managed
```

---

# 25. Create the Databricks Access Connector

```bash
az databricks access-connector create \
  --resource-group rg-mercatura-dev-uks \
  --name ac-mercatura-dev-uks \
  --location uksouth \
  --identity-type SystemAssigned \
  --tags \
    project=meridian \
    organisation=mercatura \
    environment=dev \
    managed_by=cli \
    purpose=unity-catalog-storage
```

## What it creates

An Azure Databricks Access Connector with a system-assigned managed identity.

The Azure CLI currently exposes this command through the Databricks extension. The Access Connector commands are GA. 

## Why

Azure Databricks needs an Azure identity to access ADLS.

The Access Connector provides the Azure resource through which that managed identity is associated with Databricks.

## Why system-assigned identity

Azure creates and manages the identity lifecycle alongside the Access Connector.

No client secret needs to be created, stored or rotated.

---

# 26. Retrieve the Access Connector resource ID

```bash
export ACCESS_CONNECTOR_ID="$(az databricks access-connector show \
  --resource-group rg-mercatura-dev-uks \
  --name ac-mercatura-dev-uks \
  --query id \
  -o tsv)"
```

## Why

Unity Catalog needs the Access Connector's Azure resource ID when the storage credential is created.

---

# 27. Retrieve the managed-identity principal ID

```bash
export CONNECTOR_PRINCIPAL_ID="$(az databricks access-connector show \
  --resource-group rg-mercatura-dev-uks \
  --name ac-mercatura-dev-uks \
  --query identity.principalId \
  -o tsv)"
```

## Why

Azure RBAC assigns permissions to the managed identity, not to the Unity Catalog credential.

The principal ID identifies that managed identity in Microsoft Entra ID.

## Important distinction

```text
ACCESS_CONNECTOR_ID
    identifies the Azure resource

CONNECTOR_PRINCIPAL_ID
    identifies the security principal
```

---

# 28. Grant ADLS read/write access to the managed identity

```bash
az role assignment create \
  --assignee-object-id "$CONNECTOR_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Contributor" \
  --scope "$STORAGE_ID"
```

## What it permits

Reading and writing blob/data-lake content.

## Why `ServicePrincipal`

Azure represents managed identities through service-principal objects in Entra.

The identity is still a managed identity; `ServicePrincipal` describes the principal type expected by the RBAC API.

---

# 29. Grant storage-queue access

```bash
az role assignment create \
  --assignee-object-id "$CONNECTOR_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Queue Data Contributor" \
  --scope "$STORAGE_ID"
```

## Why

Azure Databricks file-event ingestion can use Azure Storage Queues to receive file-change metadata.

This permission allows the identity to interact with those queue messages.

It does not itself grant access to file contents.

---

# 30. Grant storage-account management permission

```bash
az role assignment create \
  --assignee-object-id "$CONNECTOR_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Account Contributor" \
  --scope "$STORAGE_ID"
```

## Why

This allows Databricks to configure storage account resources required for automatically managed file events.

This is broader than blob data access and therefore exists for a different reason.

---

# 31. Retrieve the resource-group scope

```bash
export RESOURCE_GROUP_ID="$(az group show \
  --name rg-mercatura-dev-uks \
  --query id \
  -o tsv)"
```

## Why

The Event Grid role used for automatic file-event setup is scoped at the resource group level rather than only the storage account level.

---

# 32. Grant the Event Grid role used during bootstrap

The manual bootstrap used:

```bash
az role assignment create \
  --assignee-object-id "$CONNECTOR_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "EventGrid EventSubscription Contributor" \
  --scope "$RESOURCE_GROUP_ID"
```

## Why it was added

I eventually intend to use managed file events for efficient Auto Loader file discovery.

Event Grid routes Azure storage change notifications toward queue-based notification infrastructure.

## Documentation review note

Current Microsoft Azure Databricks documentation is inconsistent about the exact role required for automatically managed file events.

One current external-location setup guide specifies:

```text
EventGrid EventSubscription Contributor
```

while other current Databricks file-event guidance specifies:

```text
EventGrid Data Contributor
```

Therefore this role assignment must be resolved before Terraform encodes the final target state.

The runbook preserves the actual command that was executed.

---

# 33. Remove temporary human blob access

```bash
az role assignment delete \
  --assignee-object-id "$CURRENT_USER_OBJECT_ID" \
  --role "Storage Blob Data Contributor" \
  --scope "$STORAGE_ID"
```

## Why

I needed direct storage access only to perform bootstrap operations.

Leaving the permission would create a path that bypasses Unity Catalog governance.

The intended architecture is:

```text
developer
    ↓
Unity Catalog
    ↓
ADLS
```

not:

```text
developer
    ↓
ADLS directly
```

---

# 34. Define ADLS URLs

```bash
export MANAGED_URL="abfss://managed@${STORAGE_ACCOUNT}.dfs.core.windows.net/"
export LANDING_URL="abfss://landing@${STORAGE_ACCOUNT}.dfs.core.windows.net/"
```

## What is `abfss://`?

`abfss` is the secure Azure Blob File System URI scheme used for ADLS Gen2 access.

The URI identifies:

```text
container
storage account
path
```

For example:

```text
abfss://landing@storageaccount.dfs.core.windows.net/
```

---

# 35. Create the Unity Catalog storage-credential definition

```bash
cat >/tmp/mercatura-storage-credential.json <<EOF
{
  "name": "mercatura_dev_storage",
  "azure_managed_identity": {
    "access_connector_id": "${ACCESS_CONNECTOR_ID}"
  },
  "comment": "Managed identity for Project Meridian development ADLS access."
}
EOF
```

## What it does

Creates a temporary JSON request body.

## Why use JSON

The Databricks CLI supports structured request bodies for API operations.

Using JSON is clearer than placing complex nested values directly on a command line.

## Security

The file contains the Access Connector resource ID but no storage account key or client secret.

It is still removed after use because it is only a temporary bootstrap artefact.

---

# 36. Create the Unity Catalog storage credential

```bash
databricks storage-credentials create \
  --json @/tmp/mercatura-storage-credential.json \
  --profile mercatura-dev
```

## What it creates

```text
mercatura_dev_storage
```

inside Unity Catalog.

## What it represents

The storage credential tells Unity Catalog:

> Use this Azure managed identity when accessing authorised storage locations.

The credential does not itself define which cloud path is accessible.

---

# 37. Delete the temporary request file

```bash
rm /tmp/mercatura-storage-credential.json
```

## Why

Temporary bootstrap artefacts should not remain on disk unnecessarily.

---

# 38. Inspect the storage credential

```bash
databricks storage-credentials get \
  mercatura_dev_storage \
  --profile mercatura-dev
```

## Why

Creation succeeding is not sufficient evidence that things are done as intended. So I verify the resulting Unity Catalog object.

---

# 39. Validate access to managed storage

```bash
databricks storage-credentials validate \
  --storage-credential-name mercatura_dev_storage \
  --url "$MANAGED_URL" \
  --profile mercatura-dev
```

## What this tests

It checks whether the Unity Catalog storage credential can successfully access the specified Azure path.

This validates several layers at once:

```text
storage credential
→ Access Connector
→ managed identity
→ Azure RBAC
→ ADLS
```

---

# 40. Validate access to landing storage

```bash
databricks storage-credentials validate \
  --storage-credential-name mercatura_dev_storage \
  --url "$LANDING_URL" \
  --profile mercatura-dev
```

## Why test each location separately

A credential can be valid while permissions differ between storage paths.
Testing boundaries independently makes troubleshooting easier.

---

# 41. Create the managed external location

```bash
databricks external-locations create \
  mercatura_dev_managed \
  "$MANAGED_URL" \
  mercatura_dev_storage \
  --comment "Managed storage root for Project Meridian development data." \
  --profile mercatura-dev
```

## What it creates

A Unity Catalog external location named:

```text
mercatura_dev_managed
```

## What an external location represents

Overall:

```text
cloud storage path
+
storage credential
=
governed storage boundary
```

The external location does not itself become a table or volume.

It is an administrative storage securable.

---

# 42. Create the landing external location

```bash
databricks external-locations create \
  mercatura_dev_landing \
  "$LANDING_URL" \
  mercatura_dev_storage \
  --comment "External landing storage for Mercatura development source files." \
  --profile mercatura-dev
```

## Why a separate external location

Although both locations use the same Azure identity, they represent different data governance boundaries:

```text
managed platform storage
external source landing
```

This allows their policies to diverge later.

---

# 43. Inspect external locations

```bash
databricks external-locations list \
  --profile mercatura-dev
```

## Why

Verifies that both Unity Catalog storage boundaries exist.

---

# 44. Define the catalog managed-storage root

```bash
export CATALOG_STORAGE_ROOT="${MANAGED_URL}mercatura_dev"
```

Resulting structure:

```text
abfss://managed@<storage-account>.dfs.core.windows.net/mercatura_dev
```

## Why use a subpath

The entire `managed` container does not need to belong to a singular catalog.

Using a catalog specific subdirectory leaves room for additional environment or catalog roots rather than restricting myself to one.

---

# 45. Create the development Unity Catalog catalog

```bash
databricks catalogs create \
  mercatura_dev \
  --storage-root "$CATALOG_STORAGE_ROOT" \
  --comment "Development catalog for the Mercatura Data Platform." \
  --profile mercatura-dev
```

## What it creates

The development catalog:

```text
mercatura_dev
```

## Why catalog-level managed storage

Objects created below this catalog can inherit its managed-storage hierarchy.

Application code therefore interacts with names such as:

```text
mercatura_dev.silver.customer
```

instead of depending on internal Azure filesystem paths which can end up being long and messy.

---

# 46. Inspect the catalog

```bash
databricks catalogs get \
  mercatura_dev \
  --profile mercatura-dev
```

## Why

Confirms that the catalog exists and exposes its managed-storage configuration.

---

# 47. Create the first governed schema

The first schema was deliberately created using Databricks SQL:

```sql
CREATE SCHEMA IF NOT EXISTS mercatura_dev.landing
COMMENT 'Governed interface for externally produced source files.';
```

## Why only `landing`


At this point only the landing responsibility exists.

Schemas such as:

```text
bronze
silver
gold_sales
quality
ops
```

will be introduced when real responsibilities require them.

---

# 48. Create the external landing volume

```sql
CREATE EXTERNAL VOLUME IF NOT EXISTS
  mercatura_dev.landing.source_files
LOCATION 'abfss://landing@<STORAGE_ACCOUNT>.dfs.core.windows.net/source_files'
COMMENT 'Landing area for source-system files delivered to Project Meridian.';
```

## What it creates

The Unity Catalog volume:

```text
mercatura_dev.landing.source_files
```

which can be accessed through:

```text
/Volumes/mercatura_dev/landing/source_files/
```

## Why use a volume path

Databricks recommends volume paths for governed file access and for Auto Loader file discovery.

This prevents ingestion code from spreading physical Azure storage URLs throughout the codebase.

---

# 49. Managed-storage smoke test

```sql
CREATE SCHEMA IF NOT EXISTS mercatura_dev.platform_smoke;

CREATE TABLE mercatura_dev.platform_smoke.storage_test (
    id BIGINT,
    message STRING,
    created_at TIMESTAMP
);

INSERT INTO mercatura_dev.platform_smoke.storage_test
VALUES (
    1,
    'Project Meridian managed storage works',
    current_timestamp()
);

SELECT *
FROM mercatura_dev.platform_smoke.storage_test;
```

## What this proved

Successful creation and insertion verified:

```text
Unity Catalog
→ catalog managed storage
→ storage credential
→ Access Connector
→ managed identity
→ Azure RBAC
→ ADLS write

ADLS
→ managed identity
→ Unity Catalog
→ SELECT read
```

---

# 50. Remove the smoke-test schema

```sql
DROP SCHEMA mercatura_dev.platform_smoke CASCADE;
```

## Why

The smoke-test object had no lasting responsibility.

Temporary validation resources should generally be removed after their purpose is complete.

---

# 51. External-volume smoke test

```sql
LIST '/Volumes/mercatura_dev/landing/source_files';
```

## What this proved

The following path worked:

```text
Databricks
→ external volume
→ external location
→ storage credential
→ managed identity
→ Azure RBAC
→ landing container
```

This is the path future file ingestion workloads will use.

---

# 52. Inspect Azure resources

```bash
az resource list \
  --resource-group rg-mercatura-dev-uks \
  --query "[].{name:name,type:type,location:location}" \
  --output table
```

## Why

Provides a high level inventory of Azure resources created for the development environment.

---

# 53. Inspect Unity Catalog storage resources

```bash
databricks catalogs list \
  --profile mercatura-dev
```

```bash
databricks external-locations list \
  --profile mercatura-dev
```

```bash
databricks storage-credentials list \
  --profile mercatura-dev
```

## Why

These commands provide the equivalent inventory from the Databricks governance layer.

---

# 54. Resulting system

After completing the bootstrap:

```text
Azure
│
├── Resource Group
│      rg-mercatura-dev-uks
│
├── Databricks Workspace
│      dbw-mercatura-dev-uks
│
├── Access Connector
│      ac-mercatura-dev-uks
│        │
│        └── system-assigned managed identity
│
└── ADLS Gen2
       │
       ├── managed/
       └── landing/


Unity Catalog
│
├── Storage Credential
│      mercatura_dev_storage
│
├── External Location
│      mercatura_dev_managed
│
├── External Location
│      mercatura_dev_landing
│
└── Catalog
       mercatura_dev
          │
          └── landing
               │
               └── source_files
                    external volume
```

---

# 55. Why these commands will not remain the permanent deployment method

The manual CLI setup is just the initial resource provitioning and connection step

It exposed:

- resource dependencies
- identity relationships
- RBAC scopes
- governance boundaries
- storage ownership

The long term Project Meridian architecture will not depend on me executing dozens of commands correctly as this is tedious.

I will therefore move appropriate Azure infrastructure into Terraform.

However, Terraform should encode the reviewed desired state, not mechanically translate every bootstrap command done so far.

Temporary operations such as:

- temporary human Blob Data Contributor access
- random shell variables
- manual smoke-test objects

do not automatically need become permanent infrastructure, that would be wasting resources.

---

# 56. Reproduction order

The dependency order is:

```text
Azure authentication
      ↓
subscription selection
      ↓
resource group
      ↓
Databricks workspace
      ↓
ADLS storage account
      ↓
containers
      ↓
Access Connector + managed identity
      ↓
Azure RBAC
      ↓
Databricks authentication
      ↓
Unity Catalog storage credential
      ↓
external locations
      ↓
catalog
      ↓
schema
      ↓
external volume
      ↓
smoke tests
```

This sequence exists because later resources depend on identifiers and capabilities produced by earlier resources.

For example:

```text
storage credential
```

cannot be correctly configured until the:

```text
Access Connector
```

exists.

The Access Connector cannot access storage until:

```text
Azure RBAC
```

has been configured.

The external location depends on both:

```text
storage credential
+
ADLS path
```

Understanding dependency graphs generally will make Terraform substantially easier to understand and implement.

---

# 57. Troubleshooting principle

When a command fails, identify the failing layer before changing permissions.

Examples:

```text
az storage container create fails
    ↓
investigate Azure identity / data-plane RBAC

databricks storage-credentials validate fails
    ↓
investigate credential → managed identity → Azure RBAC → networking

CREATE TABLE fails in mercatura_dev
    ↓
investigate Unity Catalog privilege / catalog storage configuration

LIST /Volumes/... fails
    ↓
investigate volume privilege / external location / storage credential / Azure access
```

Do not respond to access errors by granting Owner or Contributor everywhere, that is dangerously poor security, everything must generally have least privilage access.

A better philosophy is to understand and fix the missing permission at the correct layer, rather than go overboard with broad permissions granting.

---

# 58. Security rules for reproducing the bootstrap

Do not place the following values in committed scripts or documentation unless there is a clear requirement:

- access tokens
- client secrets
- storage keys
- private keys
- credentials

Project Meridian deliberately avoids storage keys and client secrets for the ADLS integration.

Azure resource IDs are not secrets, but they should still be parameterised rather than unnecessarily hard coded.

---

# 59. Current open item — Event Grid role

The file-event RBAC role is not yet considered final.

During manual bootstrap we assigned:

```text
EventGrid EventSubscription Contributor
```

Current Microsoft documentation contains conflicting recommendations between:

```text
EventGrid EventSubscription Contributor
```

and:

```text
EventGrid Data Contributor
```

This is something that will be resolved and documented.

---