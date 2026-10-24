# Mercatura Operational Source Estate Overview

## Intention

The Mercatura operational source estate is the synthetic upstream operational source data environment responsible for providing data for the Mercatura data platform. This operational estate is representative of the core operational data from OLTP systems, and is not representative of data warehouse tables.

The ultimate intention behind creating a complex simulator is to supply realsitic source data material for:

- source discovery
- data profiling
- ingestion
- data contract enforcement
- CDC
- SCD
- reconciliation
- data quality
- data governance
- analytics

The initial estate contains the following source system entities:

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
- AVAILABILITY

---

## Platform Data Flow

```txt
operational systems
    ↓
source extracts
    ↓
/Volumes/mercatura_dev/landing/source_files
    ↓
future Bronze ingestion
    ↓
Silver
    ↓
Gold / data products
```

---

## Simulation Period

The initial simulation data range spans from 2024-01-01 to 2026-12-31.

This interval is sizable enough, providing sufficient history to demonstrate the data platform and core data features I want to express:

- customer retention
- customer inactivity and reactivation
- product pricing history
- inventory movement
- late data arrival
- slowly changing dimensions
- incremental ingestion
- periodic analysis

---

## Historical Data Consistency

The fundamental feature of the simulator to support data consistency is that event are generator from the valid state of the simulator at the event timestamp. Therefore, for example, an order on 2025-06-01 may only reference:

- customers existing by 2025-06-01
- products existing by 2025-06-01
- prices valid on 2025-06-01
- store valid from that particular channel and time

---

## Behavioural Realism

Customers are catagorised into the following behavioural archetypes:

- one time
- returning
- inactive
- reactivated
- high value

The behavioural classifications take into account the actual historical activity of customers so the classification is actually true.

---

## Baseline And Defects

The baseline simulator will have all the documented data integrity rules pass.

Defects are going to be implemented as definite scenarios. For example:

- A known rule is intentionally violated
- The affected records are identifyable and traceable 
- The source manifest records the defect

