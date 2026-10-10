# ADR-0001: Project Meridian Engineering Principles

- Status: Accepted
- Date: 2026-10-10

## Project Context

Project Meridian is a fictitious enterprise data platform modernisation programme I am completing as a major portfolio project. Project Meridian is assumed to be a modernisation initiative for a fictional company, Mercatura Group.

The underlying basis of the project originates from my experience at my UST graduate data engineering programme as an extention of the technical skills developed on this placement. Mercatura's project Meridian, therefore is my expansion upon the production data platform and professional engineering practices.

This platform will evolve across source data system simulation, ingestion, trasnformation, analytical modelling, data quality enforcement, data governance, deployment, observability, streaming, orchestration, performance engineering, and analytical consumption.

This initial ADR intends to provide the underlying enginerring principle context and phased execution of this project.

---

## Engineering Principle Decisions

Project Meridian will follow the following principles.

### Production oriented engineering

I will be designing components as though they will be operated and maintained rather than demonstrated once in isolation. A successful execution alone is not sufficient evidence of production readiness. Therefore, I am addressing this by designing components with longevity and intended future operation and maintainance.

### Learning As A Priority 

Important components will be documented and understood. I am taking extra care in providing cohesive narrative and exploration of the underlying concepts, alternative implementations, trade-offs, failure modes, and verification strategies not only as evidence of my understanding but so a beginner or intermediate level data engineer can reporduce the system without it being a black box.

### Platform Nativity Priority 

Instead of implementing custom solutions for data engineering features, I will use the mature capabilities of Databricks or well established open soure tools that already provide the appropriate functionality to implement features. Custom frameworks are considered, however I would evaluate the necessity of custom implementations. I have dictated that custom frameworks require an explict engineering or equally credible educational justification in order to be considered.

### Explicit Data Contracts

Important producer-consumer interfaces will have explicit and versioned data contracts. Schema and semantic changes will be treated as engineering changes rather than accidental pipeline behaviour.

### Quality Throughout the Data Lifecycle 

Data quality will be an underlying property that will be universally considered throughout development, rather than considered at a more final processing stage. I may employ different quality mechanisms at source data boundaries, pipeline boundaries, and persisted datasets.

### Governance From Inception 

A key engineering principle I am paying extra attention to for this project is security, ownership, lineage, and data classification. These principles will be considered throughout the development of the platform rather than implemented after the core pipelines are built.

### Failure Considerations In Designs

To reprent realistic operational conditions, malformed records, duplicate data, late data, retries, schema evolution, partial failures, and pipeline reruns are foundationally considered.

Therefore, the relevant components of the platform will define their behaviour under these conditions.

### Idempotency As A Default

Repeated pipeline executions should have intentional and testable semantics. Where idempotency is not guaranteed, the limitation will be well understood and documented.

### Observable Systems

Production components will expose enough evidence to determine whether they are healthy, failing, delayed, or producing incorrect results.

### Evidence Supported Optimisation

Any performance changes I wish to implement will be measureably implemented. First establishing a baseline performance, a hypothesis, a measurement, and an explaination. Optimisation techniques will not be applied without evidence of measurable beneficial impact on performance, and will be selected and tested in detail to justify specific optimisation implementations.

### Minimal Justified Technology

I intend to make a cohesive platform that is not wasteful in technology. Every significant dependency or platform capability will require a clear and justifyable responsibility. This is intended to control the scope of complexity for the project rather than forcing in tools to demonstrate familiarity already covered in other portfolio projects.

### Stable Production Foundations

All the critical production paths will favour stable capabilities. Any experimental features will be evaluated to avoid becoming fragile dependencies.

### Governed Business Semantics

Business metrics will have core significance. Important business metrics will have agreed canonical definitions rather than being reimplemented independently from downstream data consumers.

## Consequences

This project is a step up in technical sophistication from my previous data engineering centric projects. Therefore, project Meridian will warrant more design, testing, and documentation to demonstrate confidence and quality development. 

Therefore, development pace may be slower because the core engineering foundations and conceptual designs supersede any instantaneous or fast-paced implementation efforts. The core data architecture and overarching design will be established first before any sizable quantities of pipeline code.

In return, the resulting platform should be much more easier to reason about, test, deploy, operate, and explain with clarity.

This will involve some departure from my formal data engineering training at UST Global as I will be replacing or substantially modernising some approaches compared to my industry experience. The focus is on a contemporary engineering approach, and any substitutions of methods will be documented.

## Alternatives Considered

I have rejected notebook based implementation as the primary production model. The focus on this project is modularity, local testing, and strong software engineering discipline.

## Risks

- The project can become very complex. The scope is required to be controlled rather than maximising architecture.
- Databricks capabilities could change during the development period.

These risks can be managed through incremental development, frequent updates to ADRs, and checking documentation for changes.

---