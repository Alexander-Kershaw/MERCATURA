# ARD-0002: Unity Catalog Storage Architecture

- Status: Accepted
- Date: 2026-10-10
- Scope: Azure storage, Unity Catalog managed storage, external landing storage and Azure identity management

## Context

For project Meridian, I required a cloud storage architecture to serve as the Mercatural data platform development environment. Because I am using Azure and Databricks in conjunction, I required the platform to support two fundamentally distinct classes of data:

1) Data owned and managed by the Mercatura data platform itself 
2) Files produced outside of the Databricks environment that are to be delivered to the platform for ingestion.

These are different classes of data since they have different lifecycles and individual governance requirements. 

Specifically, the data owned by the Mercature data platform on Databricks (analytical tables for example) are goverened and have their lifecycle managed through Unity Catalog whenever that is possible.

Whereas, the externally produced files are registered as externally managed objects since their lifecycle can be controlled by source systems, upstream producers or ingestion processes existing outside of Databricks.

This is ultimately the distinction between managed and external tables. 

Furthermore, the architecture avoids embedding Azure storage keys, client secrets or other sensitive credentials in any code or repository configurations. 

Moreover, the development environment is constructed in such a way that it is relatively inexpensive while simultaneously preserving the underlying architecture that can later be hardened for production once I am more satisfied with the status of the project. Otherwise, I risk hemorrhaging my budget for this project on expensive infrastructure that would be unnecessary for the current development phase.

## Design Decisions

I will be using Azure Data Lake Storge (ADLS Gen2) as the cloud object storage layer for the Mercatura development environment.

Initially I populated the development storage account with two dedicated storage containers:

- `managed/`
- `landing/`

These initial containers have indivdiual responsibilities at this point.

#### Managed

The managed container is being reserved for Unity Catalog managed data (the data owned by the Mercatural data platform itself). The Unity Catalog managed storage location is defined beneath this container for the `mercatura_dev` catalog.

Mercatura platform owned tabular data will used Unity Catalog managed tables by default unless specific requirements justify uses of external tables. Furthermore, users and external systems are not able to directly permitted to manipulate file withing this managed storage hierarchy. Therefore, the managed data is seperate and owned by Mercatura, and its authorised users and by nothing else.

#### Landing

The landing container represents the externally managed source files delivered to Project Meridian. A Unity Catalog external location governs the access to this storage container. Specifically, an external Unity Catalog volume exposes the source file landing area to Databricks users and workloads with: `/Volumes/mercatura_dev/landing/source_files/`.

Note that some producers could eventually write to an Azure storage location with appropriately scoped Azure identities. Also note that the external volume registration is done so Databricks consumers interact with the governed volume rather than directly interacting with the underlying ADLS Gen2 storage container `abfss://` path.

## Unity Catalog Experiment Boundary

I have established the development catalog in Unity Catalog / Databricks as:
`mercatura_dev`. The managed storage root resides under: `abfss://landing@stmercaturadev9756f9.dfs.core.windows.net/mercatura_dev`. The environment-oriented catalog is the primary logical isolation boundary for Project Meridian development data.

Future environments will follow the same conceptual pattern as such: 

```txt
mercatura_dev
mercatura_test
mercatura_prod
```

Howver, the exact Azure topology for test and production environments will ultimately be decided seperately.

## Azure Identity Model

Azure Databricks accesses ADLS Gen2 storage through a Databricks Access Connector using a managed identity assigned by the system.

The identity chain is as follows:

```txt
Unity Catalog
      │
      ▼
Storage Credential
      │
      ▼
Databricks Access Connector
      │
      ▼
System-assigned Managed Identity
      │
      ▼
Azure RBAC
      │
      ▼
ADLS Gen2
```

The Unity Catalog storage credential does not contain a storage key or a client secret. It just references the Azure Databricks Access Connector resource. Then Azure RBAC determines the storage operations the managed identity is permitted to perform. The Unity Catalog permissions seperately determine which Databricks principles have permission to use the governed storage objects.

## Unity Catalog Object Model

The current storage abstraction implemented is formed of the Unity Catalog objects, forking into managed and landing locations (managed being owned by Unity Catalog / Databricks, and landing being a registered external volume in ADLS Gen2):

```txt
Azure Managed Identity
        │
        ▼
mercatura_dev_storage
Storage Credential
        │
        ├───────────────────────────┐
        ▼                           ▼
mercatura_dev_managed        mercatura_dev_landing
External Location            External Location
        │                           │
        ▼                           ▼
catalog managed storage      source_files external volume
```

##### Storage Credential

The storage credential `mercatura_dev_storage`, has the following responsibilities:

- represents the Azure managed identity to Unity Catalog
- contains no embedded storage keys or client secrets
- can be referenced by multiple external locations

##### Managed external Location

The managed external location `mercatura_dev_managed` is responsible for:

- registering the ADLS managed container as a governed cloud storage boundary
- permitting a subpath to be used as managed storage for `mercatura_dev`

##### Landing external Location

The external landing location `mercatura_dev_landing` is responsible for:

- registing the ADLS landing container as a governed cloud storage boundary
- supporting externally produced source files in ADLS Gen2

##### External Landing Volume

The external landing volume `mercatura_dev.landing.source_files` is responsible for:

- providing a governed file interface for ingestion
- allowing future workloads such as using Audo Loader to consume externally produced files
- Avoids exposing any raw cloud storage container paths to the data engineering code that will be developed.

##### Managed vs External Assets

To be more formal with the distinction between managed and external data assets, the distinction lies more on the lifecycle ownership rather than whether Unity Catalog provides governance. Both the managed and external Unity Catalog assets are governed objects. However:

- For a managed table or managed volume, Unity Catalog determines the underlying storage location and ownership of the lifecycle of the associated files. So Databricks controls both the table and metadata (schema and columns etc...) AND the underlying data files stored in its default cloud storage location. Typically managed tables with be using Delta Lake so they are also ACID compliant. 

- For an external table or external volume, Unity Catalog still governs the object from within Databricks, but the underlying files remain independently managed. So, Databricks manages only the metadata, and I am explicitly specificing and have control of the storage location (using ADLS Gen2 in this case). So dropping tables in the databricks SQL editor only removes the metadata, but the underlying data files remain untouched in cloud storage (ADLS Gen2). Moreover, for external volumes, there is a wider range of supported formats including Delta Lake, Parquet, CSV, JSON, etc...

Basically:

```txt
Platform-owned tabular data
        ↓
Unity Catalog managed tables

Externally produced source files
        ↓
Unity Catalog external volumes
```

This is what makes the difference on ownership explicit.


## Azure Storage Configuration

The development storage account is configured as:

- StorageV2
- hierarchical namespace enabled
- HTTPS access only
- minimum TLS version 1.2
- anonymous blob access disabled
- shared key access disabled
- public network endpoint enabled for the development environment

Enabling the hierarchical namespace is what provides ADLS Gen2 semantics, basically transforming a flot object store into a directory-based file system. So, instead of using paths with slashes like folder/subfolder/file.parquet, the hirarchical namespace enablement allows for the organisation of objects into trees of folders and nested subfolders. A key advantage of enabling hierarchical namspace when provisioning the storage account, is that atomic operations become accessible: directory level actions such as renaming, moving, and deleting folders happen instantly by updating a single parent directory entry rather than rewriting or moving millions of individual files. This is advantageous for this project since I will be using frameworks like Apache Spark and Databricks, which often like to rename temporary output directories at the end of a job. With the hierarchical namespaces, the renaming becomes atomic and fast which reduces job latency and costs.

HTTPS only access just means that unencrypted HTTP traffic is rejected access to the storage. Secure transfer is required.

The minimum TLS (transport layer security) version is pinned at 1.2. This is a security baseline. This means that anly client application, script, or tool attempting to connect to the Azure storage using a TLS lower than version 1.2 will be blocked. The older TLS versions lack the modern cryptographic algorithms and are vunerable to exploits making the older versions less secure. TLS is important as it is a cryptographic security protocol intended to protect data privacy in integrity for internet communications. The encryption disguises data so third parties and hackers cannot read it, so intercepted data is unreadable. Authentication is another pillar of TLS, it proves that the server being connected to is actually who it claims to be, this prevents spoofing attacks where a hacker can pretent to be my Azure cloud storage portal. Furthermore, TLS support data integrity, using ditigal signatures, it ensures that data has not been modified while traversing across a network.

Anonymous blob access is disabled so public read permissions on my cloud storage cannot happen. Valid login or security tokens are required to read files in the cloud storage. Anyone with a direct link to a file or gaintainer within my Azure storage configuration cannot open it without authorization first. This is good practice to avoid data leaks, attackers cannot use automated scripts or brute forcing tools to steal files stored in my containers either.

Shared key authentication is intentionally disabled so the project Meridian relies on identity based access rather then using account keys all the time.

Public network access remains enabled in the development environment to avoid prematurely introducing private networking and incuring network infrastructure costs. Later in development, a production environment will evaluate privat endpoints, network isolation, and VNet-integrated Databricks architecture seperately.

## Azure RBAC model

The access connector managed identity receives the Azure permissions requires for Databricks storage access. The core Azure permission being granted is the Storage Blob Data Contributor permission. Additional storage/event permissions are used to prepare the landing area for file-event-based ingestion. The current environment includes the following permissions:

- Storage Queue Data Contributor
- Storage Account Contributor 
- EventGrid EventSubscription Contributor

These permissions will be codified with infrastructure as code (Terraform). Before that, the event grid permission assignment is to be reviewed againt the current Azure Databricks documentation when the time comes.

The current documentation specifies EventGrid Data Contributor instead. This will be reviewed and potentially changed if necessary.

## Human Access

I am using the development user as the human access which was temporarily granted the Storage Blob Data Contributor permission in oder to initially create the ADLS containers using Microsoft Entra authentication. I removed the direct storage role after creating the containers. I have done this since platform users should not have parallel direct access paths that bypass Unity Catalog governance.

The access path I am enforcing is the following:

```txt
Human / workload
      │
      ▼
Unity Catalog privilege
      │
      ▼
Table or Volume
      │
      ▼
External Location
      │
      ▼
Storage Credential
      │
      ▼
Managed Identity
      │
      ▼
Azure RBAC
      │
      ▼
ADLS
```

In future, the external source produces will each receive seperate appropriately scoped identities rather than using the developer Azure identity for everything.

## Development Storage - Account Topology 

The development environment is using a single storage account with seperate managed and landing containers.

I have done this since this means I am using fewer Azure resources, has simpler administration, and is sufficient for a portfolio level development environment.

However, I will note that containers in a single sorage account will share account-level scalability limitations. Furthermore, managed and externally produced workloads are not phyically isolated as they exist within the same storage account. This means that any incidents or configuration changes to the storage account impacts both the landing and managed containers.

A larger scale production architecture would typically use seperate storage accounts for managed and external landing storage. I may evaluate this as part of a later production-reference infrastructure design.

## Data Layer Implications

The medallion architecture layers I intend (bronze, silver, gold) as logical data lifecycle concepts (each will have different data lifecycle policies), and will not automatically be mapped to seperate Azure containers.

The physical cloud storage structure does not have to be dependent on the logical medallion naming conventions. I can have bronze, silver, and cold ultimately coexist within the Unity Catalog managed storage hierarchy as:

- `mercatura_dev.bronze`
- `mercatura_dev.silver`
- `mercatura_dev.gold`

## DBFS Policy

The project will not use DBFS (Databrick File System) mounts as the primary mechanism for cloud storage access.

I am using Unity Catalog managed storage, external locations and volumes as the storage access.

## Verification

I verified the achitecture with two smoke tests.

##### Managed storage test

I created a temporary schema and managed Delta table under `mercatura_dev.platform_smoke` and a record was successfully inserted and queried.

This verified the access chain:

```txt
Databricks principal
→ Unity Catalog catalog
→ managed storage root
→ storage credential
→ managed identity
→ Azure RBAC
→ ADLS
```

##### External volume test

I created an external volume `mercatura_dev.landing.source_files` and was listed through its Unity Catalog volume path.

This verified the access chain:

```txt
Databricks principal
→ Unity Catalog volume
→ external location
→ storage credential
→ managed identity
→ Azure RBAC
→ ADLS landing container
```

## Alternatives Considered

##### Storage account keys

I rejected this approach as using long-lived credentials requires rotation and would weaken the identity-based security model I want to enforce.

##### Service principal with client secret

I rejected this for the primary storage path. Although, this is a valid approach in some architectures, it also introduces secret lifecycle management, which is unnecessary when Azure managed identities are avaliable.

##### Direct `abfss://` access

Rejected since direct paths expose explicity cloud storage implementation details and also encourage bypassing the governed Unity Catalog objects.

##### External tables for all data

I rejected this alternative. The platform owns analytical data and should use managed tables by default so on Databricks Unity Catalog can manged both the governance and storage lifecycle.

##### Seperate development storage accounts for managed and landing data

I have deferred this alternative for now. This approach does provide stronger physical isolation of data assets but doesnt add much value at the current scale of the project.

## Consequences of decisions

### Benefits

- No storage account keys are applications secrets are required making the implementation more simple
- Azure access is identity-based
- Unity Catalog is the primary governance layer
- Platform and external ownership of data assets are seperated and have explicit lifecycle boundaries
- The future source ingestion implementation can use a stable governed volume
- The architecture can advance towards a stronger production isolation without having to change the core governance model

### Negatives

- Troubleshooting requires understandong of both Azure RBAC and Unity Catalog permissions
- Two independent authorisation system can produce superficially similar access failures
- The development storage account is not network-isolated
- A single development storage account shares scalability limits across both the landing and managed containers
- The file-event RBAC needs to be reviewed before implementing any IAC

### Risks

- Direct Azure permissions could potentially allows a user to bypass Unity Catalog which can break governance
- Broad Unity Catalog priveledges could harm storage governance
- managed storage paths could end up corrupted if manipulated directly outside of Unity Catalog
- IAC could preserve to temporary bootstrapped permissions unless roles are explicitly reviewed
- The physical storage architecture risks requiring expansion as the workload volume increases

## Later ADR considerations

Later ADRs probably should address the following:

- IAC strategy
- environment topology for test and production
- source producer identiy 
- network isolation
- schema topology within `mercatura_dev`
- file ingestion stragegy
- data quality architecture



