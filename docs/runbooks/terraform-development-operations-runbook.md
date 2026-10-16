# Terraform Development and Operations Runbook

## Intetion

This runbook covers the workflow I used after the initial infrastructure as code foundation. It is designed to provides specific clarification and exact commands used for the following:

- Initialising the Terraform environment
- Authenticating correctly
- Inspecting infrastructural drift
- Making infrastructure changes
- Reviewing plans and applying plans safely
- Troubleshooting state and provider issues
- Running static checks

## Preconditions

The following local tools are required:

```txt
Terraform
Azure CLI
Databricks CLI
Git
```

Furthermore, the project repository must contain:

```txt
infrastructure/terraform/environments/dev/
scripts/check-terraform-static.sh
```

Access to the following is also necessary:

- Azure access to the development subscription
- Databricks workspace access
- Membership of the `mercatura-dev-platform-admins` group for administrative Terraform operations
- Access to the Terraform remote backend container

---

## Authenticate to Azure

Terraform is using the AzureRM provider and the Azure Blob backend uses the Azure CLI authenticated identity, therefore it is necessary to login:

```bash
az login
```

The verify the active subscription:

```bash
az account show \
  --query "{name:name,state:state}" \
  --output table
```

if necessary the Azure account can have the subscription set with:

```bash

az account set --subscription "<subscription-name>
```

---

## Authenticate to Databricks

For this project, I am using `mercatura-dev` as the local workspace profile. The Databricks profile must be authenticated since the Databricks Terraform provider reuses this profile.

This profile is verified with:

```bash
databricks current-user me \
  --profile mercatura-dev
```

If the authentication needs to be refreshed use:

```bash
export DATABRICKS_HOST="https://$(az databricks workspace show \
  --resource-group rg-mercatura-dev-uks \
  --name dbw-mercatura-dev-uks \
  --query workspaceUrl \
  --output tsv)"

databricks auth login \
  --host "$DATABRICKS_HOST" \
  --profile mercatura-dev
```

---

## Setting Terraform Environment Variables

Core Terraform environment variable such as Azure subscription and ADLS storage account names should be exported as environment variables to avoid hard coding environment variables. If the configuration requires an existing role assignment identifyer, this can be retrieved from Azure.

For example, set the Azure subscription with:

```bash
export TF_VAR_subscription_id="$(az account show --query id -o tsv)"
```

An existing ADLS storage account name can be set with:

```bash
export TF_VAR_storage_account_name="<DEV-STORAGE-ACCOUNT-NAME>"
```

in `.tfvars` no environment specific values should be committed to the repository.

---

## Backend Configuration

A local `backend.hcl` is created. `backend.hcl.example` can also be create to be committed, the actual backend should not be commited, just the example.

The expected shape of the `backend.hcl`:

```hcl
storage_account_name = "<terraform-state-storage-account>"
container_name       = "tfstate"
key                  = "dev/azure.tfstate"
```

---

## Initialise Terraform

Initialisation is done by changing to the dedicated terraform directory and running the following:

```bash
cd infrastructure/terraform/environments/dev

terraform init \
  -backend-config=backend.hcl
```

If provider versions require updating, the following command can be used, however upgrades are not to be done casually and should move within provider version contraints:

```bash
terraform init -upgrade \
  -backend-config=backend.hcl
```

---

## Formatting

Terraform formatting comes before establishing a plan:

```bash
terraform fmt -recursive
```

---

## Validation

```bash
terraform validate
```

Validation is used to check provider resource schemas, references, types, and the consistency of the terraform configuration. Terraform validate does not inherently prove that the infrastructure operation will be succesful.

---

## Static Repo Gate

From the repository root run:

```bash
./scripts/check-terraform-static.sh
```

This performs terraform validation in an isolated temporary directory without the requirement of cloud credentials. This is to be run before pushing any Terraform changes.

---


## Live Drift Check

```bash
terraform plan -detailed-exitcode
```

Followed by `echo $?`

should retrun exit code 0 for a successful terraform plan with no infrastructural drift detected.

---

## Making an Infrastructural Change

Edit the HCL. Then use Terraform format and validation

```bash
terraform fmt -recursive
terraform validate
```

To save a terraform plan, this is done with:

```bash
terraform plan -out=change.tfplan
```

Reviewing this saved plan should be intentional. Before even considering applying the plan, some key questions should be answered such as:

- What is being added?
- What is being changed?
- What is being destroyed?
- Is anything being replaced?
- Are the changes in the expected provider / control plane?
- Are the privileges becoming too broad
- Are stateful resources being affected?

---

## Apply The Reviewed Plan

```bash
terraform apply change.tfplan
```

This applys the saved terraform plan. Then remove the local plan file with:

```bash
rm -f change.tfplan
```

Afterwards, run

```bash
terraform plan
```

Ideally, the plan should return zero drift.

---

## Inspecting Terraform State

The resources managed in a terraform stated can be listed with:

```bash
terraform state list
```

Individual resources can be inspected, e.g:

```bash
terraform state show databricks_catalog.dev
```

It is important to note that

```bash
terraform state show
```

shows the stored representation of the Terraform state. This is not a substitude for inspecting the provider platform when troubleshooting any issues.

---

## Inspecting Azure State

Example of inspecting the Azure state are as follows:

```bash
az group show \
  --name rg-mercatura-dev-uks
```

```bash
az storage account show \
  --name "$TF_VAR_storage_account_name" \
  --resource-group rg-mercatura-dev-uks
```

```bash
az role assignment list \
  --scope "<RESOURCE-ID>"
```

Inspecting Azure states with the Azure CLI is more useful when a problem can be traced to the Azure control plane.

---

## Inspecting Databricks State

Examples of inspecting the Databricks states are:

```bash
databricks catalogs get \
  mercatura_dev \
  --profile mercatura-dev
```

```bash
databricks storage-credentials get \
  mercatura_dev_storage \
  --profile mercatura-dev
```

```bash
databricks groups list \
  --profile mercatura-dev
```

Inspecting Databricks states with the Databricks CLI is beneficial when issues are tracable to Databricks itself. Use Databricks state inspections before changing Terraform states when a Databricks authorisation problem occurs, the issue can be diagnosed with the Databricks states.

---

## Unity Catalog Owner Verification

The current owner of the platform securables is `mercatura-dev-platform-admins`.

The owner of resources can be showed with the following checks:

```bash
terraform state show databricks_catalog.dev | grep owner
terraform state show databricks_schema.landing | grep owner
terraform state show databricks_volume.source_files | grep owner
terraform state show databricks_storage_credential.dev | grep owner
terraform state show databricks_external_location.managed | grep owner
terraform state show databricks_external_location.landing | grep owner
```

---

## Grant Verification

Within the SQL editor in Databricks workspace, the following queries can be executed:

```sql
SHOW GRANTS ON CATALOG mercatura_dev;

SHOW GRANTS ON SCHEMA mercatura_dev.landing;

SHOW GRANTS ON VOLUME mercatura_dev.landing.source_files;
```

These queries show the grants established on some core resources. These grants are associated with the data engineer group. 

The grants currently given to the data engineer group include:

```txt

USE CATALOG
USE SCHEMA
READ VOLUME
```

---






