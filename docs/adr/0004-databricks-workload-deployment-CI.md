# ADR-0004: Databricks Workload Deployment and CI Strategy

- Status: Accepted
- Date: 2026-10-17
- Scope: Databricks workload packaging, declarative automation databricks bundles, serverless compute jobs, CI identity, CI development, platform and unity catalog smoke testing

## Context

Prior to the content covered in this ADR, I have established the core Mercatura data platform infrastructural foundations: Azure infrastructure has been represented in Terraform, a remote Terraform state backend was implemented, Unity Catalog resources were represented in Terraform, Group based Unity Catalog ownership was established, least privilege grants were attributed to the data engineer identity group, and a cloud credential-free Terraform static CI was also implemented.

With that foundation established and validated, it was time to prove that application code could be packaged from the repository, deployed to Azure Databricks, executed on serverless compute, authenticated using a CI identity, permitted access to the governed Mercatura data via Unity Catalog, and validated automatically after deployment.

Therefore, I had forked the development, giving a conspicuous separation between cloud / platform infrastructure, workload deployments, application code, and runtime identity.

---

## Decision 

I proposed that the following deployment layers be implemented and adhered to:

- Terraform: owning the durable Azure and Unity Catalog platform infrastructure
- Declarative Automation Bundles: owning deployable Databricks workload definitions
- Python wheel: containing the executable application code
- GitHub Actions: for validation, deployment, and smoke testing the CI target
- Microsoft Entra Workload Identity: for authenticating GitHub Actions without the need of long-lived secrets

---

## Bundle Engine

I am using the direct deployment engine in the Databricks bundle deployment model:

```yaml
bundle:
    engine: direct
```

The bundle deployment engine is independent from the Terraform configuration used for platform infrastructure. I am not using the Terraform bundle deployment engine as this has been retired.

---

## Python Packaging

I am packaging the application logic as a Python wheel built with `uv build --wheel`. The bundel artifact configuration performs this build during deployment. 

Executable entry points were exposed through `pyproject.toml`. These initial entry points expose smoke tests for the platform and unity catalog access with `platform_smoke` and `catalog_smoke`. 

I am doing deployment this was since I want a more production quality flavour to this project. Hence, I am deploying importable and testable Python packages, rather than embedding production logic directly into Databricks notebooks.

---

## Serverless Compute

The Databricks jobs run initially on a serverless job compute. The serverless environment was referenced in the Python wheel tasks using `environment_key: default`.

However, dependencies for serverless tasks are declared at the environment level rather then at the task level. The pattern was therefore change to:

```yaml
tasks:
  - task_key: example
    python_wheel_task:
      package_name: mercatura
      entry_point: example
    environment_key: default

environments:
  - environment_key: default
    spec:
      environment_version: "4"
      dependencies:
        - ../dist/*.whl
```

This meant that the serverless tasks were appropriately declared at the environment level. This decision follows an initial deployment failure where the wheel was incorrectly declared in the task-level block which returned the following Databricks error: `Libraries field is not supported for serverless task, please specify libraries in environment.`.

The configuration was corrected to the correct pattern shown above, rather than departing from using serverless compute.

---

## PySpark Dependency

PySpark was not packaged as a dependency for the serverless Databricks workloads. This is because Spark is already supplied in the Databricks execution environment by default. Therefore, application code obtains the runtime spark session rather than bundling in a seperate PySpark distribution with the application code.

---

## Development Artifact Versioning 

Dynamic artifact versioining was used for the development and CI targets. The source package is semantically versioning in `pyproject.toml`. For example, in `pyproject.toml` I have version `0.1.0`, while in deployment, the development artifacts recieve a dynamic local version such as `0.1.0+1792228819141148075`.

This avoids serverless dependency caching treating multipel changed environment builds as the same wheel version. The production releases will differ from the development builds. For production, I will use deliberate release versions rather than depending on the development dynamic versions.

---

## Deployment Targets

Two bundle targets are currently defined: `dev` and `ci`. 

##### `dev`

The purpose of the `dev` bundle target is to serves as the interactive developer deployment, which is owned by me. It is used for local experimentation and development, and local `bundle run`. It uses `mode: development` and therefore receives Databricks development-mode isolation behaviour.

##### `ci`

This bundle target is used for automated GitHib deployment. Instead of being owned by me, it is owned by the CI service principle identity. It is used for stable integration deployment, and for automatic governed smoke testing at this stage.

The CI target does not use `mode: development`. This is because the Databricks development mode enforces a resource prefix derived from the developer username as a way to guarantee per-developer uniquness. The CI target is not a developer environment. Instead it is one stable automated development owned by one single workload identity.

## Bundle Identity

A deployable bundle is identified by the combination of bundle name + target + deployer identity. 

The `mercatura dev` deployment associated with my personal developer identity, is seperate from the `mercatura ci` deployment that uses a workload service principle identity. Therefore, these seperate deployments are not forced to share the same root path, they are kept obviously seperate.

## Ci Identity

GitHub Actions is authenticated using a dedicate Microsoft Entra service principal `sp-mercatura-github-dev`. The authentication uses GitHib OIDC feberation, rather than relying on long-lived Azure client secrets, any Databricks PATs, Databricks client secrets, or requirements for any storage account keys.

Therefore, the authentication path resembles the following: 

```txt
GitHub Actions
    ↓ GitHub OIDC token
Microsoft Entra ID
    ↓ federated credential
Mercatura CI service principal
    ↓ Azure CLI authenticated context
Databricks CLI
    ↓ Azure CLI authentication
Azure Databricks workspace
```

---

## Service Principal Authorization 

The CI service principal is not a member of the `mercatura-dev-platform-admins` group. Instead I made it a member of the `mercatura-dev-data-engineers` group. Therefore the CI service principle inherits the data engineer group Unity Catalog permissions:

```txt
USE_CATALOG
    mercatura_dev

USE_SCHEMA
    mercatura_dev.landing

READ_VOLUME
    mercatura_dev.landing.source_files
```

The CI service principle therefore has no broad platform administration rights since this is unecessary just to deploy and execute jobs. This is another example of me using least privilege permissions on identities.

---

## Run-as Identity 

The CI bundle target explicitly sets the service principle as the jobs `run_as` identity. This is just explititly defining the identity associated with the execution. The deployed job therefore tests the permissions of the machine identity (the service principal), instead of the permissions of myself who authored the repository.

---

## CI Quality Gates

The Databricks development workflow performs a series of local software quality checks before obtaining any cloud credentials. This is so the time and the scrope for which the workflow holds a cloud identity is minimized. The general quality gate flow is as follows:

```txt
checkout
    ↓
uv install
    ↓
pytest
    ↓
ruff check
    ↓
ruff format --check
    ↓
pyright
    ↓
only then authenticate
```

---

## CI Bundle Lifecycle

The automated development is sequenced into a number of chronological execution order steps:

```txt
bundle validate
    ↓
bundle plan
    ↓
bundle deploy
    ↓
bundle summary
    ↓
verify deployed job through Jobs API
    ↓
run smoke job through Jobs API
```

The CI workflow serializes the deployments using the GitHib Actions concurrency controls.

---

## Post-deployment Execution 

I intended the Databricks Bundle lifecycle to unclude using `bundle run`. However, despite the CI passing the the jobs being confirmed to be running and executing within Databricks, `bundle run` failed. Specifically, this chain of events was observed:

```txt
bundle deploy                    succeeds
bundle summary                   resolves catalog_smoke
resources.json                   contains catalog_smoke
jobs list                        shows catalog_smoke
jobs get                         succeeds
jobs run-now                     succeeds
bundle run -t ci catalog_smoke   fails with "resource not found or not yet deployed"
```

It is apparent that the resources were in fact deployed and visible, so nothing is functionally going wrong and the expected behaviour and outcomes still occured.

For now, the current CI execution patterns is the following:

```txt
bundle summary
    ↓
extract deployed job ID
    ↓
databricks jobs get
    ↓
databricks jobs run-now
```

This keeps the bundles responsible for deployment while using the native jobs interface for post-deployment execution. This could be an issue with Databricks CLI, and potentially resolved with upgrading it.

---

## Smoke Tests

##### Platform Smoke

This smoke test coveres packaging the deployment path:

```txt
Python source
→ wheel build
→ artifact upload
→ serverless dependency install
→ Python entry point
```

The job output is a report detailing the application, package version, health status, and the UCT execution time.

##### Catalog Smoke

This test covers the governed platform path:

```txt
Python wheel
→ serverless Spark
→ Unity Catalog catalog
→ Unity Catalog schema
→ external volume
→ ADLS
```

This job just performs read-only verifications (since the workload service principle identity is part of the data engineer group which only has read privileges and least privilege Unity Catalog grants). The test checks both the Unity Catalog object resolution and filesystem access via `/Volumes`. Note that this smoke jobs does not bypass Unity Catalog with a raw ADLS Gen2 storage container path `abfss://`, instead it adheres to the established Unity Catalog / Databricks paths exposed in `/Volumes`.

---

## Source of Truth Policy

The repository is the source of truth for the bundle managed jobs. Any changes that are made are to be made through Git -> Validationi -> plan -> deploy, rather than via manual job edits in the Databricks workspace UI.

Although, the Databricks UI is very useful for inspecting runs, logs, and the execution history, as well as debugging and resource observation. It is not the place where changes are made, this avoids relying on Databricks notebooks for everything.

---

## Alternatives Considered

##### Databricks Notebooks as the predominant deployment unit

This has been rejected for the cohesive production logic I am going for in the project. Notebooks are still useful for exploration, demonstrations, and performing any analysis. However, for production logic, any serious implementation will be done with importable Python modules accompanied by tests.

##### Deploy raw python source code without packaging

This was also rejected. The Python wheel approach provides explicit build artifacts, package metadata, and executable entry points. This is much more appropriate for a production environment than just deploying source code without any formal packaging.

##### Classic Compute Clusters

I did not select this for the foundation of the smoke jobs. Serverless compute ultimately provides a simpler operational baseline for the current use case.

##### Store a Databricks PAT in GitHib Secrets

Rejected this. I elected to use an OIDC workload identity which removes the need for storing a long-lived Databricks secret.

##### Store an Azire Client secret in GitHub

Also rejected. Again, the GitHub OIDC federation removes the need for keeping a long-lived Entra client secret around.

##### Make CI a platform admin

Rejected. The smoke test in itself proves that the workload can operate using least-privilege principles. The data engineer group rights are sufficient for running these smoke tests.

##### Share the `dev` bundle root with CI

This was rejected. Human and machine deployments should have independent ownership and states.

##### Switch from the direct engine due to the `bundle run` failure

This was rejected. Since every other direct engine operation was successful and the deployed job executes correctly via the Jobs API. The observed error is likely isolated to something other than deployment correctness. 

---

## Consequences

### Positives

- Now have repeatable Databricks deployment from Git
- Have testable Python package achitecture 
- serverless job execution 
- secretless CI identity
- least priviledge runtime authorisation
- human and machine deployment isolation
- governed data access verification
- deployment and execution are independently verifiable 
- No dependency on development to be within notebooks 

### Negatives

- Additional set up with CI identity federation
- `bundle run` currently not used for CI execution due to a resolution issue


---

## Future Considerations

The future work on the project should probably consider production/staging bundle targets, production release versioning, deployment approval gates, job permissions, scheduled workflows, Lakeflow pipelines, CI workload identiy for authenticated Terraform planning, and retesting the `bundel run` after Databricks CLI upgrade, and immutable deployment folders for production wherever it may be justified.

---

## Summary

- Terraform builds the platform infrastructure
- Declarative automation bundles deploy workloads
- Mercatura python wheel contains executable code
- GitHub workload identity performs the automated deployment 
- Unity Catalog governs the runtime data access

A key win for this part of the project is that I have established a reproducible deployment change, that is both secretless, and in alignment with least privilege principles. 