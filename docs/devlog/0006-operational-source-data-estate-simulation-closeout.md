# Project Meridian — Phase 1 Closeout

| Metadata | Value |
|---|---|
| Organisation | Mercatura Group |
| Programme | Project Meridian |
| Phase | 1 — Operational Source Estate |
| Status | Complete / Frozen |
| Next phase | Source discovery, contracts and extraction |

## 1. Summary

This initial phase of the project has successfully delivered a deterministic multinational operational source estate for the Mercatura Data Platform.

The estate integrates independent operational domains through coherent business relationships, temporal dependencies, financial transactions and physical inventory movements.

The completed implementation provides 30 observable source datasets and one internal simulation dataset across 11 commercial markets.

The canonical estate build successfully completed its complete estate reconciliation, and the source exporter produces UTF-8 JSONL artefacts accompanied by a simulation manifest.

The operational simulator is now considered frozen. Subsequent development will focus on acquiring, validating, integrating, governing and serving the generated data.

## 2. Delivered capabilities

| Workstream | Deliverable | Status |
|---|---|---|
| Simulation foundation | Configuration, deterministic random streams, simulation identity, clock and identifier generation | Complete |
| Retail estate | International store master and lifecycle | Complete |
| Product estate | Global products, market assortments and temporal pricing | Complete |
| Demand simulation | Shared latent demand profiles | Complete |
| Supplier estate | Supplier master, capabilities and sourcing agreements | Complete |
| Procurement | Purchase orders, supplier fulfilment, shipments and receipts | Complete |
| Warehouse estate | Warehouse topology, logical locations, stocking relationships and inbound routing | Complete |
| Inventory foundation | Opening balances, receipt and putaway movements | Complete |
| Customer estate | Customer master, lifecycle and loyalty membership | Complete |
| Commerce | Omnichannel orders and transaction-time pricing | Complete |
| Payments | Market-aware payment attempts, retries, capture and void outcomes | Complete |
| Fulfilment | Requests, allocation, reservation, picking and dispatch | Complete |
| Reverse logistics | Customer returns, restock, quarantine and write-off | Complete |
| Refunds | Financial refund execution and captured-payment reconciliation | Complete |
| Availability | Market-assortment ATP and stock-risk snapshots | Complete |
| Estate orchestration | Canonical dependency-aware source-estate builder | Complete |
| Reconciliation | Cross-system commercial, financial and inventory controls | Complete |
| Export | UTF-8 JSONL serialization and simulation manifest | Complete |


## 3. Verification evidence

| Verification | Evidence | Result |
|---|---|---|
| Automated test suite | 927 tests passed before final packaging tests were added | PASS |
| Final packaging tests | successful validation | PASS |
| Ruff | successful lint checks | PASS |
| Ruff formatting | successful formatting checks | PASS |
| Pyright | successful static type checking | PASS |
| Canonical estate build | Full three year source estate execution | PASS |
| Estate reconciliation | Canonical reconciliation report | PASS |
| Source export | Successfully generated JSONL artefacts | PASS |
| Unicode export | Exporter updated to use `ensure_ascii=False`; artefacts regenerated | PASS |


### 3.1 Reproduction commands

Execute the standard engineering gates:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

Execute the canonical source estate build:

```bash
uv run python -m mercatura.source.estate.build
```

Execute without producing export artefacts:

```bash
uv run python -m mercatura.source.estate.build --no-export
```

Execute the estate integration test:

```bash
MERCATURA_RUN_FULL_ESTATE=1 \
uv run pytest \
  tests/integration/source/estate/test_complete_source_estate.py \
  -v
```

## 4. Architectural decisions retained

| Decision | Rationale |
|---|---|
| Independent operational domains | Creates meaningful downstream integration and ownership boundaries |
| Deterministic generation | Supports reproducible engineering experiments and regression testing |
| Valid baseline by construction | Separates genuine defects from expected business outcomes |
| Explicit temporal semantics | Enables historical reconstruction and point-in-time analysis |
| Local monetary values retained | Prevents destructive currency standardization |
| Native Unicode retained | Preserves multilingual source identity and meaning |
| Physical inventory represented as a signed ledger | Enables balance reconstruction and reconciliation |
| Reservations separated from physical movement | Preserves correct available-to-promise semantics |
| Latent demand excluded from operational exports | Prevents synthetic information leakage |
| JSONL used as canonical interchange format | Provides a simple source-preserving export boundary |
| External FX reference data deferred | Keeps international reporting responsibilities outside the operational simulator |
| Source simulator frozen before ingestion development | Prevents diminishing returns from unnecessary operational complexity |

Supporting detail is maintained in the architecture documents, source-estate specifications and applicable ADRs.

## 5. Known modelling limitations

The following limitations are intentional scope boundaries rather than unresolved implementation defects.

| ID | Limitation | Analytical consequence | Extension trigger |
|---|---|---|---|
| LIM-001 | Warehouse ledger excludes store-level inventory movements | Cannot reconstruct complete enterprise physical stock | Store-inventory analytics becomes a defined requirement |
| LIM-002 | Customer returns originate from outbound shipments | In-store returns are not comprehensively represented | Omnichannel reverse-logistics analysis |
| LIM-003 | Simplified order pricing | Comprehensive discount, promotion and tax analysis is unsupported | Detailed commercial margin modelling |
| LIM-004 | No financial general ledger | Operational revenue cannot be represented as audited accounting revenue | Financial consolidation becomes a project objective |
| LIM-005 | No supplier invoice or accounts-payable lifecycle | Complete procure-to-pay analysis is unsupported | Supplier financial-performance use case |
| LIM-006 | No warehouse-to-warehouse transfers | Inventory-network redistribution is not represented | Network optimization use case |
| LIM-007 | Market-level timezone defaults | Multi-timezone markets are simplified | More granular event-origin temporal requirements |
| LIM-008 | Availability generated for a specific snapshot date | Historical stock-risk trends are not directly supplied | Inventory snapshot or streaming use case |
| LIM-009 | Completed-world source exports | Exported records may contain lifecycle information unavailable at earlier observation dates | Point-in-time extraction and incremental ingestion |
| LIM-010 | Synthetic operational distributions | Data is suitable for engineering demonstrations, not empirical retail-market research | External benchmarking becomes necessary |
| LIM-011 | Date-level precision for some operational events | Exact intraday event ordering cannot always be reconstructed | Subdaily operational analytics |
| LIM-012 | No external FX reference feed | Enterprise GBP reporting requires additional reference data | Silver financial conformance |
| LIM-013 | No full source mutation or CDC history | Arbitrary historical source changes cannot be reconstructed | CDC and incremental extraction exercises |


## 6. Technical debt register

The following register records engineering improvements that may become necessary as the platform evolves.

Priority indicates when an item should be considered, rather than an immediate requirement to expand Phase 1.

| ID | Area | Technical debt or improvement | Risk | Priority | Resolution stage |
|---|---|---|---|---|---|
| TD-001 | Simulation identity | Entity identifiers are scoped to the simulation identity, which includes generation configuration | Comparing entities across scenario variants may be difficult | Medium | Scenario testing |
| TD-002 | Source export | Manifest does not currently contain per-file cryptographic checksums | Cannot independently establish byte-level delivery integrity | High | Extraction contracts |
| TD-003 | Source export | Export writes directly into the target directory | Interrupted execution may leave partial output | High | Extraction reliability |
| TD-004 | Schema management | Physical schemas are defined primarily by Python dataclasses | Downstream consumers lack independent versioned contracts | High | Phase 2 |
| TD-005 | Aggregate typing | `SourceEstate` uses generic `tuple[object, ...]` dataset collections | Consumers of the aggregate lose entity-specific static typing | Low | Only if downstream code requires stronger typing |
| TD-006 | Reproducibility | Independent deterministic replay and checksum comparison has not been evidenced | Reproducibility claims are not fully verified at artefact level | Medium | Extraction validation |
| TD-007 | Reconciliation | Certain estate-wide checks operate at aggregate level | Compensating record-level errors may remain undetected | Medium | Automated DQ framework |
| TD-008 | Quality metadata | Documentation-level rule catalogue is not yet executable metadata | Rule implementation and documentation may diverge | High | MDDQ implementation |
| TD-009 | International conformance | Currency precision, normalization and timezone policies are not yet enforced through source contracts | International parsing may become inconsistent | High | Source contracts and Silver |
| TD-010 | Extraction semantics | Full-world export lacks a generalized observation-cutoff mechanism | Historical ingestion may expose future-state information | High | Phase 2 |
| TD-011 | Deployment | Previously observed Databricks bundle CLI resource-lookup behaviour | CI deployment and execution workflows may require additional verification | Medium | Platform deployment |
| TD-012 | Documentation | Some architectural information exists in multiple Markdown documents | Maintenance effort and documentation drift | Low | Documentation maintenance |
| TD-013 | Performance | Complete simulator generation is relatively expensive compared with isolated unit tests | Slow feedback if full-estate generation is unnecessarily repeated | Low | CI optimization |
| TD-014 | Export security | JSONL output includes synthetic customer and payment-related attributes without production classification controls | Unsafe patterns could be carried into real-data processing | Medium | Governance implementation |

### 6.1 Debt management policy

Technical debt will be resolved when it becomes relevant to a concrete engineering objective.


## 7. Engineering retrospective

| Observation | Lesson | Application to later phases |
|---|---|---|
| Independent generators required careful dependency ordering | Data integration depends on explicit ownership and causal relationships | Model pipeline dependencies from actual data contracts |
| Temporal price changes affected transaction validity | Current-state joins are insufficient for historical data | Use effective-date joins and historical dimension policies |
| Payment retries created multiple records per order | Transaction identifiers and event grain must remain distinct | Prevent join fan-out and financial double counting |
| Reservations and physical movements required separate treatment | Related business concepts are not necessarily interchangeable measures | Define semantic meaning before developing KPIs |
| Return processing involved multiple operational systems | Business workflows cross source ownership boundaries | Design multi-source reconciliation |
| Inventory accounting required signed movement groups | Correct balances depend on conservation rules and temporal scope | Develop ledger-aware validation |
| International markets introduced language and monetary differences | Local truth must be preserved before enterprise standardization | Make international policies explicit in ingestion metadata |
| Passing tests did not establish complete business realism | Automated testing and semantic inspection complement one another | Combine technical checks with profiling and business reconciliation |
| Simulation complexity expanded rapidly | Realism must be justified by downstream engineering value | Freeze upstream scope once sufficient |
| Documentation accumulated duplication | Multiple descriptions of the same contract create maintenance risk | Prefer canonical documents and generated references |

## 8. Lessons for metadata-driven architecture

This initial development phase provides the operational foundation for two future platform capabilities.

### Metadata-driven data ingestion

The MDDI framework is intended to eventually support configuration driven source onboarding, extraction, parsing, schema enforcement, loading, audit and recovery.


### Metadata-driven data quality

The MDDQ framework will eventually execute versioned quality and reconciliation rules against governed datasets.

AI-assisted profiling and metadata generation may be introduced after deterministic contract validation and execution controls are established.


## 9. Phase 2 handover

The operational source estate becomes an upstream dependency of the data platform.

The immediate downstream work is:

| Workstream | Intended outcome |
|---|---|
| Source discovery | Identify actual fields, data types, distributions and source risks |
| Source profiling | Produce repeatable evidence about schema, completeness, uniqueness and value distributions |
| Schema contracts | Define machine-readable, versioned source interfaces |
| Extraction design | Establish source delivery patterns and observation-cutoff semantics |
| Extraction integrity | Introduce manifests, checksums and complete-delivery verification |
| Landing | Preserve source deliveries in ADLS Gen2 with appropriate metadata |
| Bronze | Establish governed, source-faithful Delta tables |
| Incremental processing | Demonstrate replay, duplicate protection, change handling and recovery |
| Quality integration | Translate selected source invariants into executable validation |
| Framework abstraction | Develop MDDI and MDDQ from demonstrated reusable patterns |


## 10. Exit assessment

| Exit criterion | Assessment |
|---|---|
| Operational domains implemented | Satisfied |
| Canonical orchestration implemented | Satisfied |
| Cross-system reconciliation passed | Satisfied |
| Source artefacts generated | Satisfied |
| International source values preserved | Satisfied |
| Source ownership documented | Satisfied |
| Entity grains documented | Satisfied |
| Business invariants documented | Satisfied |
| Known limitations disclosed | Satisfied |
| Technical debt recorded | Satisfied |
| Downstream implementation direction established | Satisfied |

Phase 1 is accepted as complete.

The remaining technical debt does not immediately prevent Phase 2 from beginning.

---

