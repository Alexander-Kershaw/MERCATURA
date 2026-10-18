# Devlog 0005 - Databricks Bundles, Serverless Jobs, and CI/CD

- Date: 2026-10-17

## Objective

I wanted to depart from working on the core underlying durable infrastructure for the Mercature data platform and establish a repeatable application deployment workflow that was not reliant on manual Databricks UI configuration or notebook use.

This development in the project was overall motivated by the desire to establish a formalised deployment methodology and implementation that can persist throughout the remainder of the project that is both robust and demonstrative of production standard deployment practices.

This increment required to prove Python packaging, Declarative Automation Bundle validation, Bundle planning, Bundle deployment, serverless Python wheel execution, Unity Catalog access from deployed code, secretless GitHub authentication, service-principal deployment, and automated post-deployment smoke testing.

## First Packaged Workload

I created a small production style Python entry point `mercatura.platform.smoke` which was exposed in `pyproject.toml`. I built the wheel locally with `uv build --wheel` resulting in the creation of `mercatura-0.1.0-py3-none-any.whl`, an exclusively Python wheel.

## First Bundle Configuration

I created `databricks.yml` and `resources/platform_smoke.job.yml` as the first bundle configuration. The bundle used direct engine and built wheel artifacts with `uv build --wheel` using `mode:development` and target `dev`.

## First Bundle Plan

The direct deployment engine produced:

```txt
create jobs.platform_smoke

Plan: 1 to add, 0 to change, 0 to delete, 0 unchanged
```

This result confirmed the deployment diff before mutation.

## Initial Deployment Failure

Initially, the deployment built the wheel successfully, uploaded it, and uploaded Bundle files. However, it failed while creating the serverless job with:

```txt
Libraries field is not supported for serverless task,
please specify libraries in environment.
```

This was found to be because the original wheel definition was at the task-level. However, for the serverless wheel job used in this case, the dependency was suggested to belong under environment: `job.environments[].spec.dependencies`. Therefore, the YAML awas corrected to satisfy this.

The corrected job structure therefore became:

```txt
task
    python_wheel_task
    environment_key
        ↓
environment
    environment_version
    dependencies
        Mercatura wheel
```

This solution appropriately established the wheel definition at the environment level and ran successfully. This correction allowed me to retain using serverless compute rather than migrating to classic compute.

## Dynamic Development Artifact Versioning

Dynamic artifact versioning was implemented at this stage. The next successful run reported version `0.1.0+1792228819141148075` which demonstrate that the development artifact versioning was now dynamic and build versions were unique as desired.

## Initial Remote Job Execution Success

To run the platform smoke job remotely I ran the following Databrick CLI command:

```bash
databricks bundle run \
  platform_smoke \
  --profile mercatura-dev
```

This ran successfully and the remote JSON output of the smoke test reported `mercatura` as the application, `status=ok`, and a dynamically versioning package build as expected.

## Governed Catalog Smoke Test

The second package entry point exposed in the `pyproject.toml` was the catalog smoke test `catalog_smoke`. The intention behind the smoke test was the verify that Python executions can work from the Mercatura wheel. Moreover, this test specifically tested a number of important execution tasks in a job by doing the following:

- Obtaining the Spark session in the development Databricks environment (spark session using serverless compute)
- Selecting `mercatura_dev` 
- Selecting `landing` storage
- Describing the `source_files` volume
- Listing entities within `Volumes/mercatura_dev/landing/source_files`
- Returning a structured smoke test success report

The combination of these tasks within the smoke test tested a multitude of paramount aspects that are significant for the remainder of the project. These being:

- Executing Spark 
- Accessing data with Unity Catalog
- Accessing external volumes
- Interacting with ADLS Gen2 storage

Bear in mind that this smoke test was a purely reading job, no data was written as part of the test which is fine since this automated test uses the dedicated CI workload identity which has membership in the data engineers group which have least privilege read-only grants.

This test was successful indicating a solid foundation to develop and deploy foundational pipeline code going forward.

## CI Workload Identity

I created a dedicated Microsoft Entra service principal `sp-mercatura-github-dev` allowing GitHib Actions to authenticate via OIDC federation, rather than depending on application client secrets being stored in GitHub secrets. 

This CI identity was then added to Databricks as an Entra-managed service principle and given membership to the `mercatura-dev-data-engineers` group giving it core data engineering least privilege permissions, rather than broader administrative platform admin group authorities which would've been excessive for the smoke test scope.

## Authentication Smoke Workflow

I created a manual GitHub workflow that requested a GitHib OIDC token, then authenticated via `azure login`, then installing Databricks CLI and running `databricks current-user me`. As expected this command returned the CI service principal identity, rather than my own personal identity.

This verified that no Databricks PAD, Azure client secrets, or personal user sessions are required for the deployment workflow to work as intended.

## CI Target Introduction

I introduced a dedicated bundle target `ci`. This target was configured using `mode:development` with a custom `[ci]` resource prefix initially.

However, local validation of this configuration failed with the following error message:

```txt
prefix should contain the current username or
${workspace.current_user.short_name}
to ensure uniqueness when using 'mode: development'
```

This actually exposed the core intention behind using Bundle development mode: per-human developer isolation.

The CI target instead one stable machine-owned integration deployment, therefore `mode:development` was removed. Dynamic artifact versioning and CI specific presets were explicitly retained.

## Human VS CI Deployment Identity

The human and CI bundle deployment resolve under different identities:

- The human developer bundle deployment is resolved under my workspace identity.

- On the other hand, the CI bundle deployment is resolved under the service principal identity.

This demonstrated that the same bundle name and target can still represent different deployments when the deployer identity (either human or machine) is different. This keeps the human `dev` and the automated machine `ci` deployment state isolated from eachother as intended.

## Initial Full Deployment Workflow

The initial deployment workflow I introduced included core quality tests, authentication, bundle deployment, followed by the catalog smoke test execution. The workflow followed this general architecture:

```txt
pytest
ruff
pyright
↓
OIDC authentication
↓
bundle validate
↓
bundle plan
↓
bundle deploy
↓
catalog smoke
```

## `bundle run` CI Failure

The CI workflow successfully ran and the jobs successfully completed when I observed runs within Databricks UI. However, despite successful deployment:

```bash
databricks bundle run -t ci catalog_smoke
```

This above Databricks CLI command failed returning `resource not found or not yet deployed`.

I introduced a diagnostic set within the established workflow. This involved an intermediate workflow task showing a summary of the Bundle including the associated job IDs for the two different smoke tests:

```txt
catalog_smoke
    job ID: 598322708643398

platform_smoke
    job ID: 907976438287241
```

The diagnostic step also included the printing of the direct deployment state files:

```txt
.databricks/bundle/ci/deployment.json
.databricks/bundle/ci/resources.json
.databricks/bundle/ci/sync-snapshots/...
```

Specifcally, `resource.json` contained `resource.jobs.catalog_smoke`. 

The jobs API was also investigated as part of the diagnostics and were visible:

```txt
598322708643398  [ci] Mercatura - Catalog Smoke
907976438287241  [ci] Mercatura - Platform Smoke
```

The combination of all the diagnostic step evidence showed with certainty that the job in fact existed, the bundle had knowledge of its job ID, and the service principle could see it.

Therefore, the conclusion was made that the error did not represent a failed deployment.


#### Jobs API Execution Workaround

I modified the workflow to the following structure:

```txt
bundle summary --output json
    ↓
extract catalog_smoke job ID
    ↓
jobs get
    ↓
jobs run-now
```

This CI job passed and the Databricks workspace showed the run completing successfully also.

This verified that deployment, job visibility, the service principal runtime identity, serverless execution, and Unity Catalog access were are functioning as intended.

## Final CI Workflow

The final CI workflow conducts the following steps:

```txt
checkout
uv setup
Python 3.12
uv sync --frozen
pytest
ruff lint
ruff formatting check
pyright
OIDC login
Databricks CLI installation
current-user verification
bundle validate
bundle plan
bundle deploy
bundle summary
Jobs API deployment verification
jobs run-now catalog smoke
```

The diagnostic block is still being retained with the intention of investigating Databricks CLI upgrades to address the error with running `databricks bundle run -t ci catalog_smoke`.

## Final Result

In conclusion, this stage of the project has demonstrated a complete production ready lifecycle.

The demonstrated workflow:

With a Git commit
- Runs software quality gates (pytest, pyright, ruff)
- Uses a secretless CI identity
- Builds the Python wheel
- Validates Bundles
- Previews deployment
- Deploys Databricks jobs
- Resolves Deployed jobs
- Executes jobs as the CI service principal identity
- Reads governed Unity Catalog volumes
- Successfully integrates smoke tests

## Takaways From This Increment

- Bundles are not the same as Terraform. Terraform deploys the underlying infruastructure while bundles deploy Databricks workloads.
- Packaging is an inherent part of deployment. A python script may work locally, however in production environments this is not sufficient. Instead, a python wheel must build, upload, install, and execute scripts remotely.
- Changes to source should change the development package identity. Hence, dynamic artifact versioning is used to prevent any state dependency caching during iterative deployment phases.
- The CI should not be a human identity. The CI has a service identity principal that has its own machine identity and associated and appropriately scoped permissions.
- Secretless authentication is quite practical. Using GitHub OIDC and Entra identity federation remved the necessity for storing long-lived CI secrets.
- The CI should adhere to least privilege permissions principles. The CI principal identity has the appropriately scoped read privileges without having adminsitrative ownership over the entire platform.
- Deployment identity is significant. Bundle name and target alone are not a complete deployment identity.

---



