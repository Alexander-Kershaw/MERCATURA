# Devlog 0002 — Azure & Unity Catalog Storage Bootstrap

- Date: 2026-10-10  
 

## Goal

Create the first governed cloud-storage layer for the Mercatura Data Platform.

The increment needed to establish:

- Azure Data Lake Storage Gen2
- separate managed and landing storage responsibilities
- identity-based Databricks access to Azure storage
- a Unity Catalog storage credential
- governed external locations
- the `mercatura_dev` catalog
- an external source-file volume
- verification of both managed and external storage access

I intentionally performed the implementation manually before introducing Terraform so that the individual Azure and Unity Catalog resources could be understood first.

---

## Starting state

Before this increment, I already had:

- a working local Python package
- `uv` dependency management
- pytest
- Ruff
- Pyright
- SQLFluff
- Git repository standards
- Azure CLI access
- Databricks CLI access
- Azure resource group:

```text
rg-mercatura-dev-uks
```

- Azure Databricks workspace:

```text
dbw-mercatura-dev-uks
```

- Premium workspace configuration
- serverless Databricks development capability
- Unity Catalog availability
- working Databricks OAuth authentication profile:

```text
mercatura-dev
```

No external Azure data lake had yet been connected to Unity Catalog.

---

## 1. Created ADLS Gen2 storage account

A globally unique Azure StorageV2 account was created in UK South.

The account was configured with:

```text
StorageV2
Standard_LRS
hierarchical namespace = enabled
HTTPS only = enabled
minimum TLS = TLS 1.2
anonymous blob access = disabled
shared-key access = disabled
public network access = enabled
```

---

## 2. Temporarily granted human data-plane access

I temporarily assigned myself:

```text
Storage Blob Data Contributor
```

on the storage account.

Creating the storage account did not inherently grant permission to perform blob/data-lake operations inside it.

The temporary role allowed the initial containers to be created using Entra authentication.

---

## 3. Created storage containers

Two ADLS containers were created:

```text
managed
landing
```

### `managed`

Reserved for Unity Catalog-managed storage.

### `landing`

Reserved for files whose storage lifecycle is controlled outside the Mercatura analytical platform.

### Important architectural decision

The containers are not:

```text
bronze
silver
gold
```

because medallion layers are logical processing concepts rather than necessarily separate Azure storage boundaries.

---

## 4. Created Databricks Access Connector

Created:

```text
ac-mercatura-dev-uks
```

using a:

```text
SystemAssigned
```

managed identity.

Two identifiers were retrieved during setup:

- Access Connector Azure resource ID;
- managed-identity principal ID.

The resource ID is referenced by Unity Catalog.

The principal ID is used for Azure role assignments.

No identifiers containing subscription or tenant information are stored in repository documentation.

---

## 5. Assigned storage permissions to the managed identity

The Access Connector managed identity received:

```text
Storage Blob Data Contributor
```

on the storage account.

This enables Databricks to read and write ADLS data.

Additional roles were added in preparation for file-event-based ingestion:

```text
Storage Queue Data Contributor
Storage Account Contributor
EventGrid EventSubscription Contributor
```

### Review discovered during documentation

During the post-implementation documentation review, current Azure Databricks guidance was checked again.

The current documented role for automatic Event Grid file-event configuration is:

```text
EventGrid Data Contributor
```

at the resource-group scope.

Therefore the existing Event Grid role assignment is considered a bootstrap implementation detail that must be reconciled before Terraform codifies the final target state.

---

## 6. Removed temporary personal storage permission

After the containers were created, the temporary:

```text
Storage Blob Data Contributor
```

assignment was removed.


Leaving direct personal access to the underlying storage would allow a parallel path around Unity Catalog.

The desired normal access model is:

```text
Developer
    ↓
Unity Catalog
    ↓
Governed object
    ↓
Azure storage
```

rather than:

```text
Developer ─────────────► Azure storage

Developer
    ↓
Unity Catalog
    ↓
Azure storage
```

External source producers will later receive dedicated identities where direct landing-zone access is intentionally required.

---

## 7. Created Unity Catalog storage credential

Created:

```text
mercatura_dev_storage
```

The credential references the Azure Databricks Access Connector.

No storage account key, password or client secret is embedded in the credential.


---

## 8. Created Unity Catalog external locations

Created:

```text
mercatura_dev_managed
```

for the `managed` container.

Created:

```text
mercatura_dev_landing
```

for the `landing` container.

Both reference:

```text
mercatura_dev_storage
```

### Concept learned

An external location combines:

```text
cloud path
+
storage credential
```

to create a governed Unity Catalog storage boundary.

The same storage credential can support multiple external locations when its Azure identity is authorised for the underlying paths.

---

## 9. Created development catalog

Created:

```text
mercatura_dev
```

The catalog uses a managed-storage subpath beneath the `managed` container.


### Why catalog-level managed storage

The catalog represents the development environment's primary data-isolation boundary.

The intended future naming pattern is:

```text
mercatura_dev
mercatura_test
mercatura_prod
```

The exact Azure resource topology for test and production remains undecided.

---

## 10. Created landing schema

Created:

```text
mercatura_dev.landing
```

The schema represents the governed interface to externally delivered source files.

Other planned schemas such as:

```text
bronze
silver
gold_sales
gold_customer
quality
ops
```

---

## 11. Created external source-files volume

Created:

```text
mercatura_dev.landing.source_files
```

backed by:

```text
abfss://landing@stmercaturadev9756f9.dfs.core.windows.net/source_files
```

The Databricks volume interface is:

```text
/Volumes/mercatura_dev/landing/source_files/
```

### Why external volume

The files placed in this area will originate outside Databricks.

Their underlying storage lifecycle therefore remains externally controlled.

Unity Catalog still governs access from Databricks.

---

## 12. Performed managed-storage smoke test

Created temporary schema:

```text
mercatura_dev.platform_smoke
```

Created a managed table:

```text
storage_test
```

Inserted a record containing the message:

```text
Project Meridian managed storage works
```

Queried the table successfully.

The temporary schema was then dropped.

### What this proved

The complete managed-table path worked:

```text
Unity Catalog catalog
    ↓
managed storage root
    ↓
storage credential
    ↓
Access Connector
    ↓
managed identity
    ↓
Azure RBAC
    ↓
ADLS
```

The successful `INSERT` proved write capability.

The successful `SELECT` proved read capability.

---

## 13. Performed external-volume smoke test

Listed:

```text
/Volumes/mercatura_dev/landing/source_files
```

successfully.

### What this proved

The external-volume path worked:

```text
Unity Catalog volume
    ↓
external location
    ↓
storage credential
    ↓
Access Connector
    ↓
managed identity
    ↓
Azure RBAC
    ↓
ADLS landing container
```

This is the path that future file-ingestion workloads will use.

---

## 14. Resulting Azure architecture

The development Azure environment now includes:

```text
rg-mercatura-dev-uks
│
├── dbw-mercatura-dev-uks
│     Azure Databricks
│
├── ac-mercatura-dev-uks
│     Databricks Access Connector
│
└── stmercaturadev9756f9
      ADLS Gen2
      │
      ├── managed/
      └── landing/
```

---

## 15. Resulting Unity Catalog architecture

```text
Storage Credential
└── mercatura_dev_storage
       │
       ├── External Location
       │     └── mercatura_dev_managed
       │
       └── External Location
             └── mercatura_dev_landing


Catalog
└── mercatura_dev
      │
      └── landing
            │
            └── source_files
                  external volume
```



---

## 16. Current project capability

Project Meridian can now:

- authenticate developers to Azure Databricks
- authenticate Databricks to Azure Storage without account keys
- create Unity Catalog-managed Delta data
- access an externally managed ADLS landing area through a governed volume
- isolate development data under the `mercatura_dev` catalog
- govern Azure storage access through a layered identity model

Project Meridian does not yet have:

- Infrastructure as Code
- production network isolation
- source-system producer identities
- Bronze/Silver/Gold schemas
- ingestion pipelines
- generated source data
- (potential) Great Expectations integration
- CI/CD deployment of Databricks resources


---

