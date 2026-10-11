<p align="center">
  <img src="assets/mercatura_header.png" alt="" width="100%">
</p>

<p align="center">
  <strong>Project Meridian — Mercatura Data Platform</strong>
</p>

<p align="center">
Project Meridian is a production oriented enterprise data engineering project
for the fictional Mercatura Group.
The project develops a modern Azure Databricks data platform spanning
operational source systems, ingestion, Delta Lake, Spark transformation,
dimensional modelling, streaming, data quality, governance, CI/CD,
observability, semantic metrics and analytical consumption.
</p>



## Status

**Phase 0 — Engineering Foundation**

Current focus: repository and development foundations.

## Engineering principles

Project Meridian prioritises:

- production oriented design
- learning and conceptual understanding
- explicit data contracts
- automated testing
- governance and quality throughout the lifecycle
- observable and recoverable pipelines
- source controlled deployment
- evidence based performance engineering
- platform native capabilities before unnecessary custom frameworks

See

[`docs/adr/0001-project-meridian-engineering-principles.md`](docs/adr/0001-project-meridian-engineering-principles.md)
for the full architectural decision.

## Local development

Requirements:

- Python 3.12
- `uv`
- Databricks CLI

Install the project environment:

```bash
uv sync
```

Then run the current quality gates:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

Build the Python distrubtion:

```bash
uv build
```

## Operational runbooks

- [Azure development environment bootstrap](../runbooks/bootstrap-azure-development-environment.md)


## Repository Structure

```txt
src/mercatura/       production Python package
tests/               automated tests
docs/adr/            architecture decision records
docs/architecture/   architecture documentation
docs/devlog/         chronological engineering journal
docs/standards/      engineering conventions
evidence/            review and programme evidence
```

The repository structure will evolve incrementally as development continues.


---

