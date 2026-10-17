# Databricks Bundle and CI/CD Architecture

## Intention

This document serves to desribe the architecture established as a result of considering Databricks Bundle deployment and CI/CD. It covers explaination of how source code, using `uv`, Python wheels, Declarative Automation Bundles, Databricks Serverless Jobs, GitHub Actions, Microsoft Entra workload identity, Unity Catalog, and ADLS Gen2 storage all integrate together.

---

## Architecture Overview

```txt
                         Git repository
                               │
                               ▼
                    Python and Bundle config
                               │
             ┌─────────────────┴─────────────────┐
             │                                   │
             ▼                                   ▼
        local developer                     GitHub Actions
             │                                   │
             ▼                                   ▼
      mercatura-dev OAuth                 GitHub OIDC token
             │                                   │
             │                                   ▼
             │                         Microsoft Entra ID
             │                                   │
             │                                   ▼
             │                         CI service principal
             │                                   │
             └─────────────────┬─────────────────┘
                               │
                               ▼
                       Databricks CLI
                               │
                               ▼
               Declarative Automation Bundle
                               │
                      validate / plan
                               │
                               ▼
                            deploy
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
        [dev] jobs                         [ci] jobs
      human deployment                  machine deployment
              │                                 │
              └────────────────┬────────────────┘
                               ▼
                      serverless job compute
                               │
                               ▼
                         Mercatura wheel
                               │
                               ▼
                           Spark session
                               │
                               ▼
                         Unity Catalog
                               │
                               ▼
          mercatura_dev.landing.source_files
                               │
                               ▼
                              ADLS
```

---

## The Layers of Responsibility

### Terraform 

Terraform still manages the underlying platform infrastructure resources such as Azure storage, Access Connector, Azure RBAC, Unity Catalog storage credentials, external locations, catalogs, schemas, volumes, and grants.

Overall, I consider Terraform to have ownership over the foundational durable infrastructure and governance resources that exist at the core of this Mercatura data plaform.

### Declarative Automation Bundles

The bundles manage deployable Databricks workload resources. These resources include: jobs, tasks, serverless environment specifications, wheel artifacts, deployment targets, and the identity run-as configuration.

Bundles serves to specific what exact Databricks application/workflow resources should be deployed. 

### Python Packaging 

The Mercatura wheel contains the executable logic. This currently includes the smoke tests: platform smoke, and catalog smoke. In future, this will include core pipeline code such as: ingestion code, data validation and transformation code, for instance. 

The Mercatura wheel as the core Python packaging method essentially defines what the deployed workload actually does.

---

## Current Repository Layout

```txt
mercatura/
├── databricks.yml
├── pyproject.toml
├── uv.lock
├── resources/
│   ├── platform_smoke.job.yml
│   └── catalog_smoke.job.yml
├── src/
│   └── mercatura/
│       └── platform/
│           ├── __init__.py
│           ├── smoke.py
│           └── catalog_smoke.py
├── tests/
├── infrastructure/
│   └── terraform/
└── .github/
    └── workflows/
        ├── terraform-static.yml
        ├── databricks-auth-smoke.yml
        └── databricks-deploy-dev.yml
```

---

## Mercatura Wheel Build Path

The build path is as follows:

```txt
src/mercatura/*
        │
        ▼
pyproject.toml
        │
        ▼
uv build --wheel
        │
        ▼
dist/mercatura-<version>-py3-none-any.whl
```

As of now, the wheel is purely Python, and is independent from platforms. This is beneficial for serverless compute since the underlying CPU architecture is not something that should be just assumed.

---

## Bundle Artifact Path

`databricks.yml` defines the wheel as a deployable artifact.

See the snippet:

```yml
artifacts:
  default:
    type: whl
    build: uv build --wheel
    path: .
```

During deployment, the following occurs:

```txt
bundle deploy
    │
    ├── executes wheel build
    ├── uploads bundle files
    ├── uploads artifact
    └── creates/updates job resources
```

---

## Local `ci` VS Automated `ci`

The local and automated `ci` are seperate deployments. The bundle identity includes myself as the deployer, and the automated identity uses the workload service principal. The deployments are different and are associated with different identities.

This is a possible reason why `bundle run -t ci` under my OAuth profile did not execute, since this actual CI automated deployment is machine owned with the service principal.

---

## Workload Identity Architecture

```txt
GitHub workflow
    │
    └── requests OIDC token
            │
            ▼
Microsoft Entra federated credential
            │
            ▼
sp-mercatura-github-dev (service principal identity)
            │
            ▼
azure/login
            │
            ▼
Azure CLI session
            │
            ▼
Databricks CLI
    DATABRICKS_AUTH_TYPE=azure-cli
            │
            ▼
Databricks workspace identity
```

With this architecture, no secrets need to be Issued to GitHub.

---

## CI workflow Architecture

```txt
checkout repository
        ↓
install uv + Python
        ↓
uv sync --frozen
        ↓
pytest
        ↓
ruff check
        ↓
ruff format --check
        ↓
pyright
        ↓
OIDC → Entra authentication
        ↓
Databricks CLI authentication
        ↓
bundle validate
        ↓
bundle plan
        ↓
bundle deploy
        ↓
bundle summary
        ↓
verify job ID with Jobs API
        ↓
jobs run-now
        ↓
catalog smoke succeeds
```

Cloud credentials are only aquired after the local quality checks have all passed.

---

## Development Concurrency 

GitHub Actions serializes CI deployments using a `mercatura-databricks-dev` concurrency group with `cancel-in-progress: false`. This prevents two deployments from racing against the same Bundle target state.


---

## Governed Data Path

The catalog smoke test accesses `/Volumes/mercatura_dev/landing/source_files` instead of using a raw ADLS Gen2 `abfss://` path.

The underlying data access chain is:

```txt
application
    ↓
Unity Catalog volume
    ↓
external location
    ↓
storage credential
    ↓
Access Connector
    ↓
Azure RBAC (role based access control)
    ↓
ADLS
```

---

## Trust Boundaries

GitHib can automate deployments as the CI service principal identity.

The CI service principal may deploy and run workloads, read landing volumes, but does not have administrative privileges across the whole Mercatura data platform.

I, as the human developer owns a seperate dev deployment.

Terraform owns the underlying durable infrastructure.

Bundles own the workload resources.

Unity Catalog controls the data access authorization.

---

## Future Target Model

In future, testing and production deployment environments shall be implemented.

The development will still be handled by me. The ci will perform automated integration validation.

A test/staging environment will include a shared pre-production validation.

Then the production environment will involved controlled production deployment.

---