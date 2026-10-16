# Terraform Foundation Guide

## Intention

The intention behind this guide is to explain and justify the terraform foundations that have been implemented, why they are important, the underlying concepts, and reasoning.

Furthermore, this document is intended to make the terraform implementation understandable to a degree that I can (or another developer) can reproduce and understand it from first principles.

---

## Why Terraform Was Introduced

Project Meridian has a more substantial scope than other projects and I intend it to have a very deliberate production flavour as well as a strech to my current technical capabilities. Therefore, the underlying infrastructure architecture can become complex. Furthermore, production environments and infrastructure should be reproducible. 

Initially, I created the Azure and Unity Catalog resources manually via Azure and Databricks CLI commands as part of the initial architectural bootstrapping. This was significant, as it first provided a grounded basis and understanding of the Mercatura data platform architecture before formalising it as IaC.

The initial manual infrastructure and conceptual understanding encompassed:

- Azure resource groups
- distinction between management / control plan and data plane
- ADLS Gen2 Storage
- Azure managed identities
- Azure RBAC
- Databricks Access Connectors
- Unity Catalog storage credentials
- external locations
- managed storage
- external volumes

I the introduced Terraform after the core infrastructural relationships and dependencies were throughly conceptualised and understood.

The core discipline I wanted to enforce in this project is to first understand, build, verify, then automate core infrastructure to very deliberately grasp its purpose and intention.

---

## Core Terraform Concepts

Terraform possesses three important views of infrastructure. These being the configuration, the real infrastructure, and the state.

#### Configuration

HCL describes the desired infrastructure state. An example of this is declaring the landing storage container resource:

```hcl
resource "azurerm_storage_container" "landing" {
  name                  = "landing"
  storage_account_id    = azurerm_storage_account.data.id
  container_access_type = "private"
}
```

This basically means, a private container named `landing` should exist in the storage account ID provided.

#### Real Infrastructure

The real infrastructure is the actual Azure or Databricks object.

#### State

A state is like an infrastructural snapshot or mapping which can describe the current infrastructure, or the desired infrastructure after a mutation to the Terraform configuration (or imported and adopted from existing infrastructure).

For example: 

```txt
azurerm_storage_container.landing
        ↕
real Azure landing container
```

The state is not Azure in itself. Therefore, deleting the state file does not delete Azure resources. However, without a state, Terraform between the configuration and the real resources that exist.

---

## Providers

In isolation, Terraform does not have an inherent understanding of how Azure or Databricks works. Providers are what enriches Terraform with contextual understanding of cloud and data platforms.

In this project, I use two providers:

- `hashicorp/azurerm`
- `databricks/databricks`

Providers essentailly convert Terraform resources operations into platform API calls, bridging the Terraform language to actual infrastructure operations. 

```txt
Terraform Core
    │
    ├── AzureRM provider
    │       ↓
    │      Azure
    │
    └── Databricks provider
            ↓
         Databricks
```

---

## Resources and Data Sources

Resources and data source are different in terms of where ownership of the lifecycle lies.

#### Resource

For resources, Terraform has ownership of the lifecycle. Via Terraform, operations such as creation, reading, updating, and deleting are used and can be subject to defined lifecycle protection.

Overall, the management of the resource is associated with Terraform.

#### Data source

Data sources are different from resources. For data sources, Terraform reads something, but does not have ownership of it. Essentially, Terraform reads an infrastructure object, and exposes is attribute to Terraform.

In this project, data sources are used for the serverless Databricks workspace since the provider did not currently represent the existing real infrastructure configuration faithfully enough for confident lifecycle ownership.

---

## Why Existing Resources Were Imported

Since the Azure and Unity Catalog infrastructure already existed before incorporating Terraform. Resources and data sources were imported and adopted into plans.

without importation, Terraform could end up creating another object unecssarily or recreating unfaithfully. Terraform essentially would see that a configuration says a resource should exist, but the state could contradict claiming the resourse does not exist.

Import tells Terraform that a Terraform resource is an actual existing real object and should be treated as such.

---

## The Importance Of Infrastructural Drift

Resource importation and subsequent adoption plans ideally just exclusively contain instances of imports, rather than adding, changing, or destroying resources:

```txt
6 to import
0 to add
0 to change
0 to destroy
```

Exclusive imports prove:

- Terraform had found the intended resources
- The configuration matched the existing environment
- The import would not mutate infrastructure

This exact principle was used for the imporation of Unity Catalog resources / data sources.

A core safe practice is reviewing the Terraform plan against the objective reality of the existing infrastructure before applying changes.

---

## Terraform Plans

Terraform plan is central to implementing changes to infrastructure because of what it describes.

Terraform plan compares the configuration, to the state, to the provider's observed reality, and from that comparison, proposes a transition.

Terraform plan creates an execution plan, which allows me to preview exactly what changes Terraform will make to infrastructure before any real modifications are carried out.

---

## Saved Plans

Terraform plans can be saved, and usually its beneficial to do so. Saving a plan allows for a more thorough review before applying the proposed changed the plan describes.

Without a saved plan, Terraform computes a new plan at apply time.

---

## Remote States

I moved the Terraform state from local to a remote backend.

A local state does work, however it comes with a multitude of problems such as:

- only one machine has the authoritative plan file
- accidental deletion can lose plans
- collaboration becomes difficult
- concurrent operations cannot coordinate safely

Therefore, I migrated Terraform states to a dedicated Azure Blob Storage account.

---

## Backend Storage

Since the Mercatura data platform ADLS storage account is in itself managed by Terraform. I needed to have the Terraform plan files be stored in a different account.

This is because Terraform manages the Mercatural ADLS storage account, so keeping the Terraform plan files within the same storage account would be a circular dependency issue and fragile. Furthermore, the sate recovery would be coupled to the very resource that under its management.

So instead, the Terraform backend storage, and Mercatura data storage were isolated in seperate resource groups and storage accounts to safely isolate failure domains to improve recoverability.

---

## HSN Disabled On Backend

ADLS hierachical namespace is very useful for analytical data. However, a Terraform state is just a Blob object. SO ordinary Blob Storage features such as versioning and locking were implemented instead for the Terraform state storage since they are different workloads requiring different storage design considerations.

---

## State Versioning

State versioning matters because every successful Terraform update can write a new state object. With Blob versioning, previous versions are retained. This provides a vital recovery path is an incorrect state version is written making the infrastructure recoverable. Soft delete also provides another recovery layer by stopping Terraform state from being accidentlly deleted.

---

## State Locking

State locking prevents concurrent write operations. The AzureRM backend uses Blob locking so only one writer owns the state lock at a time. This avoids infrastructure being edited simultaneously and creating issues.

---

## Backend Entra ID

Throughout the project I avoid using storage account keys, SAS tokens, and any long lived secrets wherever it is practical. Instead, I elected to use the following authorisation chain:

```txt
human identity
    ↓
Microsoft Entra authentication
    ↓
Azure RBAC
    ↓
tfstate container
```

This makes authorisation explicity and revocable is necessary.

---




