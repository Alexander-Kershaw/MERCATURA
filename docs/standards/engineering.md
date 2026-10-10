# Engineering Standards

---

## Development

For project Meridian, I will employ incremental development practices and rigourous test driven engineering wherever practical.

Any changes are to satisfy the following:

- Have a clear purpose
- Preserve or deliberately revise existing contracts
- Include appropriate automated tests
- Pass repository quality gates
- Update relevant documentation
- Be committed as a coherent unit of development work

## Python 

- Python 3.12 is the supported local runtime
- All production code is situated under `src/mercatura`
- Public interfaces use type hints where useful
- Preference fo clear functions and modules over excessive abstration
- Avoid hidden global state
- Preference for determinstic behaviour where practical

## SQL

- SQL will be in the Databricks dialect and departures from this are explicitly documented
- Queries are concerned with correctness and readability before implementing any optimisations
- Business logic will have one authoritative canonical implementation where possible
- Performance changes / optimisation implementation require definite evidence to support its usage

## Testing

Testing will be a core underlying requirement I have set out for this project. The testing discipline will be demonstrated in full.

The project may use:

- unit tests
- property and invarient tests
- contract tests
- data quality tests
- reconciliation tests
- integration tests
- pipeline tests
- regression tests
- performance tests
- end to end accpetance tests

Tests will be intended to verify and explain intended system behaviour rather than implemented for the sake of increased coverage.

## Notebooks

Although notebooks are not the core development principle. They have appropriate use for the following:

- exploration
- experiments
- demonstrations
- educational purposes
- interactive investigations

Any production logic will be implemented as importable modules.

## Data

Since I am generating source data, this will be deterministic where practical. Valid source generation and deliberate defect injection will be seperate concepts. Production transformations will define the relevant behaviour for reruns, duplicates, malformed records, schema changes, and late arriving data.

## Documentation

Architecture documentation is intended to effectively describe the current implemented system. Any significant architectural changes will be documented in ADRs. The development history and troubleshooting discoveries will be recorded in the devlog.

## Security

Credentials and secrets will never be committed to the repository. Furthermore, access will follow least privilage principles and sensitive data will be deliberately classified and cencored.

## Definition of Done

I am defining a change as being complete when the following aspects are satisfied:

- Implementation is understandable
- Relevant automated tests pass
- Linting and static checks pass
- Expected and failure behaviour is understood
- Relevant documentation is updated
- No credentials or generated artefacts are tracked
- Changes form a coherent Git commit

---
