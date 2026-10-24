# ADR-0005: Operational Source Simulation Architecture

- Status: Accepted
- Date: 2026-10-23

## Context

With the completion of the core underlying infrastructure, databricks workflow structure, and CI/CD implementation, I require a realistic operational source data simulator. This simulator will generate the source data for ingestion, initial data profiling, data contract construction, CDC, SCD, basis for reconciliation, data quality scoping, and analytics potentiality.

The objective is to model a syntehtic operational source data estate rather than constructing an array of independent CSV generators, since this might cause issues with historical consistency and temporal validity (such as orders occuring before a customer or product exists) which can happen with independently constructor simulator elements.

---

## Design Choice

The simulator will be deterministic and aware of events. Therefore the simulator will model distinct source systems that have explicit ownership boundaries, entity lifecycles, temporal rules, extraction patterns, and controlled data defect scenarios the data quality and contract rules will address.

Fundamentally I want the simulation to be internally valid, with invalid records introduced explicitly through named and intentional defect scenarios.

---

## Initial Source Systems

The set of source systems I am constructing the simulation around include:

- CRM
- LOYALTY
- PIM
- PRICING
- STORE
- OMS
- PAYMENTS
- RETURNS
- WMS
- PROCUREMENT
- AVALIABILITY

Ownership is going to be explicit. Every record belongs to the operational system that would plausibly create and maintain it. For instance:

```txt
CRM          customer profile
LOYALTY      loyalty membership
PIM          product master
PRICING      effective-dated prices
OMS          order lifecycle
PAYMENTS     payment lifecycle
RETURNS      return lifecycle
WMS          inventory state/events
PROCUREMENT  supplier and purchase-order lifecycle
```

Another ownership consideration is that the downstream data warehouse design is not to leak data backwards into source generation.

---

## Timeline Generation

The interdependency of source system events are being heavily considered in the simulator logic. All dependent events are generated against the state of the simulated world at their event timestamp. This avoids independently choosing random dates and foreign keys which harms temporal continuity of events and relational integrity.

An example timeline look like:

```txt
order timestamp
    ↓
eligible customers existing at that timestamp
    ↓
eligible products existing at that timestamp
    ↓
valid channel/store context
    ↓
order generated
```

---

## Determinism 

Determinism is a core consideration in the simulator logic. Determinism is controlled with a set of deterministic variables such that given the same variable configuration, the simulator produces the same output. Any randomness is not accepted unless it is centralized and seeded.

For example, given the same:

- generator version
- deterministic seed
- configuration
- start date
- end date
- scenario set

The simulator outputs will be the same and reproducible with the same deterministic configuration set.

---

## Simulation Context

Simulation context further allows for the internally consistent generation of source operational data. A shared simulation context will expose the following:

- Simulation ID
- Seed
- Date range / clock
- Deterministic random source
- ID generation strategy
- scenario configuration
- defect configuration

---

## Temporal Integrity

The simulator is to obey temporal continuity. Causal relationship between source system entities are to be consistent and logically rational. For example:

```txt
customer.created_at <= order.created_at

product.created_at <= order_item.created_at

order.created_at <= payment.authorized_at

payment.authorized_at <= payment.captured_at

order.fulfilled_at <= return.requested_at

store.opened_at <= STORE order timestamp
```

The above integriry rules will be enforced with extensive testing

---

## Behavioural Model

Customer behavioural logic will be modelled not just as archetypes but as core simulation policies. The classification of the customer archetype is justified by their historical generated activity. 

---

## Defect Policy

The generator in itself is to generate valid data. Defects are created via named scenarios such as:

```txt
DQ-CUST-001  duplicate customer identity
DQ-TEMP-001  order before customer creation
DQ-TEMP-002  payment before order
DQ-INV-001   negative inventory
```

For each of the intentional defects, there is an associated rule, source system, expected counts / rate and downstream detector.

---

## Extraction Model

Naturally, different source systems have different source interfaces such as:

- a full snapshit
- an incremental transaction feed
- an event food
- effective date change feed
- periodic snapshots

Note that the simulator is not producing the Bronze tables. I am keeping a strict boundary that is as follows:

```txt
source simulation
    ↓
source extract
    ↓
landing volume
    ↓
future Bronze ingestion
```

---

## Source Manifest

Each simulation / data exportation run will include a wealth of metadata:

- simulation ID
- generator version
- seed
- date range
- source system
- feed
- extract type
- record count
- creation timestamp
- active scenarios
- intentional defects

---

## Validation

The validation will be performed categorically. This will allow precise validation across different quality considerations I have for the project. These validation catagories include:

- schema / contract
- referential
- temporal
- lifecycle
- reconciliation
- behavioural
- determinism

All the validation tests are to pass before moving forward in development.

---
