# Mercatura Source Extraction Model

## Purpose

The simulated operational systems emit source extracts, not complete warehouse tables.

### Extract Identity

Each source system extract has:

- source system
- feed
- extract type
- logical extract timestamp
- data files
- manifest

This will have the following layout:

```txt
<source_system>/
  <feed>/
    extract_date=YYYY-MM-DD/
      <data-file>
      _manifest.json
```

### Snapshot

Snapshots express what the system currently has existing within it at some instantaneous moment.

A snapshot could include something like:

- CRM customers
- PIM products
- STORE estate
- WMS inventory positions
- Suppliers

### Incremental Transaction Feed

The incremental transaction feed contains source records that have been created or changed since the preceding extraction boundary.

The incremental transaction feed is used for entities and data fields that are expected to have lots of creation and update instances such as:

- orders
- returns
- purchase orders

The incremental transaction feed requies timestamp metadata to describe incremental extraction boundaries:

- `source_created_at`
- `source_updated_at`
- `extract_timestamp`

### Event Feed

An event feed is for collecting source system events that are oriented around appends. 

Example of event feed extractions include:

- payment events
- inventory events
- avaliability events

Each event requires stable event IDs since file ordering as a means of ordering events should not be treated as the order of the underlying business events being captured.

### Effective-dated Feed

Effective-dates feeds will be used initially for pricing:

- product_id
- price
- currency
- effective_from
- effective_to
- source_updated_at

This extraction method supports future as-of joins and SDC2 implementation.

### Business and Extraction Timestamps

Considering:

- order created:      10:14
- source extracted:   10:30

These are different, order creation timestamp is a business fact, wheras the source extraction timestamp is an operational extraction fact. 

Separating the two allows for data freshness and late record arrival analysis.

### Late Arrival

This is a case when a record is historically valid but arrives later than expected, for example: 

- business event: 2026-01-10
- extract arrival: 2026-01-12

This is not the same as temporal invalidity, late arrivals happen likly due to latency or some operational failure but does not void the validity of the event.

### Invalid Formats

Initially CSV will be the supported format, with later addition of JSON and Parquet.

### Manifest

Example manifest structure:

```json
{
  "simulation_id": "sim_...",
  "source_system": "OMS",
  "feed": "orders",
  "extract_type": "incremental",
  "extract_timestamp": "2026-01-01T00:30:00Z",
  "generator_version": "0.1.0",
  "seed": 42,
  "record_count": 1000,
  "files": ["orders_20260101_003000.csv"],
  "scenarios": [],
  "defects": []
}
```

### Landing Boundary

- The simulator will create source extracts
- The publicer places the extracts into `/Volumes/mercatura_dev/landing/source_files`
- Ingestion reads from the landing volume and builds the Bronze layer

---
