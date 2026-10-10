# Contributing to Project Meridian

## Workflow

Changes should normally be developed on a focused branch created from `main`.

Example:

```bash
git switch main
git pull
git switch -c feat/source-simulator
```

## Branch Naming

Use the following naming conventions: 

```txt
feat/<purpose>
fix/<purpose>
test/<purpose>
docs/<purpose>
refactor/<purpose>
perf/<purpose>
ci/<purpose>
chore/<purpose>
```

Examples:

```txt
feat/order-lifecycle
test/customer-contract
perf/sales-skew
docs/data-quality-strategy
```

## Commit Discipline

Before committing run the following:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

Also run additional SQL, integration, data quality or platform checks when relevant to the change applied.

### Commit Expectations

Please use small, coherent commits using the conventional prefixes.

For example:

```txt
feat: add deterministic customer generation
test: add temporal order invariants
fix: preserve late inventory events during deduplication
docs: record data quality architecture decision
perf: reduce sales aggregation shuffle
ci: validate bundle configuration on pull requests
```

Avoid using vague commit messages.

### Architecture Decisions

Create an ADR when any design decisions does the following:

- Materially shapes the architecture
- Establishes a new engineering policy
- Selects between alternative implementation choices
- Would otherwise be difficult to understand later

ADRs are not necessary for any trivial implementation decisions.

### Generated Files and Secrets

Avoid committing:

- Credentials
- Access tokens
- Private keys
- Local environment files
- Build outputs
- Caches
- Generated data unless used as a test fixture

