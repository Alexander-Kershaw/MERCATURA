# Databricks Bundle Development and Deployment Runbook

## Intention

I have created this runbook to demonstrate the normal operational workflow I used for the development, validation, deployment, and verification of Mercatura data platform Databricks workloads.

This runbook provides enough instructruction and CLI examples to assist in future development needs and for a person reviewing this project. It covers: modification to bundle configuration, adding Databricks jobs, adding and changing a Python wheel entry point, deploying local development targets, diagnosing CI deployment, validating service principal access, or verification of jobs (the smoke jobs in this case).

## Tools and Profiles Used

The local tools suite includes:
- Databricks CLI
- uv
- Python 3.12
- Git

The Databricks profile I use is `mercatura-dev`

The repository root should contain the following to perform the operations detaild in this document:

- `databricks.yml`
- `pyproject.toml`
- `resources/`
- `src/`

Throughout this project I conduct a number of local software checks, I typically execute the following before running any Databricks operations:

```bash
uv sync --frozen
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

If the local package quality gates fail, then the focus should be on resolving that before graduating to debugging any Databricks deployments.

---

## Wheel Building 

To build the wheel, run:

```bash
uv build --wheel
```

You can verify the wheel `.whl` has in fact been created with:

```bash
ls -lh dist/
```

---

## Testing Entry Point

The entry point can be tested locally with `uv run` for example:

```bash
uv run platform_smoke
```

For the platform smoke test in particular, `status=ok` and `application=mercatura` is expected.

The governed `catalog_smoke` test requires a Databricks Spark runtime environment and is therefore no expected to run on a local non-Spark process, it should be executed within Azure Databricks.

---

## Validating The Bundle

Validating the developer can be done with:

```bash
databricks bundle validate \
  -t dev \
  --profile mercatura-dev
```

The validation output should pass.

---

## Previewing The Deployment

The bundle plan may be inspected with:

```bash
databricks bundle plan \
  -t dev \
  --profile mercatura-dev
```

The adds, changes, plans, and unchanged resources detailed in the plan output should be inspected and understood well before deployment.

---

## Deployment Target

To deploy a Databricks bundle, execute the following:

```bash
databricks bundle deploy \
  -t dev \
  --profile mercatura-dev
```

In this case, I am deploying the developer target. Deployment may build the wheel, upload artifacts, create/update Databricks resources, sync files, and such...

---

## Inspecting Deployment

A summary of the deployed bundles can be inspected with:

```bash
databricks bundle summary \
  -t dev \
  --profile mercatura-dev
```

The returned URLs can be used to inspect jobs in the Databricks workspace.

---

## Running Smoke Jobs (For dev)

For the platform smoke check:

```bash
databricks bundle run \
  -t dev \
  platform_smoke \
  --profile mercatura-dev
```

For the catalog smoke test:

```bash
databricks bundle run \
  -t dev \
  catalog_smoke \
  --profile mercatura-dev
```

This is for the local human dev target.

---

## Note: Do Not Deploy the machine owned CI target locally

Running this:

```bash
databricks bundle deploy -t ci --profile mercatura-dev
```

With the `ci` profile from my `dev` account (human account) will mutate the `ci` deployment that is human owned rather than the machine owned deployment.

---

## Local CI Validation

The CI configuration can be validated locally by providing the service principal application identifier and exporting it with: 

```bash
export BUNDLE_VAR_ci_service_principal_name="<CI-SERVICE-PRINCIPAL-APP-ID>"
```

Then running:

```bash
databricks bundle validate \
  -t ci \
  --profile mercatura-dev
```

This allows the configuration to be checked without making the human identity the CI deployer that should be machine identity.

---

## CI Deployment Verification

First I verify the GitHub service principal identity. The CI uses `databricks current-user me` and the result of this command must identify the CI service principal and not my personal user.

Running:

```bash
databricks bundle summary \
  -t ci \
  --output json
```

Extract the job with:

```bash
JOB_ID="$(
  databricks bundle summary \
    -t ci \
    --output json |
  jq -r '.resources.jobs.catalog_smoke.id'
)"
```

Validate with:

```bash
test -n "$JOB_ID"
test "$JOB_ID" != "null"
```

Then:

```bash
databricks jobs get "$JOB_ID" >/dev/null
```

The CI governed smoke job can be run with:

```bash
JOB_ID="$(
  databricks bundle summary \
    -t ci \
    --output json |
  jq -r '.resources.jobs.catalog_smoke.id'
)"

databricks jobs run-now \
  "$JOB_ID" \
  --timeout 30m
```

The remote jobs can be inspected with:

```bash
databricks jobs list
```

Specific jobs are retrieved by using the job id:

```bash
databricks jobs get "$JOB_ID"
```

The jobs also can be inspected in the Databricks workspace in detail too.


---

## Overall developer CLI sequence

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright

databricks bundle validate -t dev --profile mercatura-dev
databricks bundle plan -t dev --profile mercatura-dev
databricks bundle deploy -t dev --profile mercatura-dev
databricks bundle run -t dev catalog_smoke --profile mercatura-dev
```





