# Devlog 0001 — Repository Bootstrap

**Date:** 2026-10-06

## Goal

Establish Project Meridian as a reproducible Python software project before
introducing Databricks specific application code.

## Work completed

- Initialised the Git repository.
- Created the `mercatura` Python package using a `src` layout.
- Configured Python 3.12.
- Added dependency management with `uv`.
- Added pytest and coverage support.
- Added Ruff linting and formatting.
- Added Pyright static type checking.
- Added SQLFluff configured for the Databricks SQL dialect.
- Added an initial package import test.
- Verified that the Python distribution builds successfully.
- Confirmed availability of Databricks CLI 1.19.0.

## Verification

The following checks completed successfully:

```text
pytest:
1 passed

ruff check:
All checks passed

ruff format --check:
3 files already formatted

pyright:
0 errors, 0 warnings, 0 informations

uv build:
source distribution built successfully
wheel built successfully

Databricks CLI:
v1.19.0
```

## Concepts

### `src` package layout

All production code is isolated under `src/`, this is so tests check the installed package rather than importing modules directly from the repository root.

### Distribution and import package

The project distribution and the python import namespace are related, but are distinct concepts.

The python package is imported as `import mercatura`

### Development vs runtime dependencies

Engineering tools such as pytest, Ruff, Pyright and SQLFluff are the development dependences, these do not need to become runtime dependencies of the data platform.

### Build verification

Successfully creating a wheel and source distribution proves that the package configuration is internally coherent and distributable.

## Problems Encountered

No failues in implementation occured at this stage.

## Next Step

I will be establishing repository governance, documentation strcuture, architecture decision records, and contribution conventions before introducing any Databricks authentication or workspace resources.

