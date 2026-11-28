# Mercatura Source Estate — Invariants and Reconciliation


## 1. Purpose

This document defines the logical integrity requirements of the Mercatura operational source estate.

These requirements intend to establish the conditions under which source data can be considered internally consistent. Furthermore, they also provide the foundation for downstream source contracts, automated data quality checks, reconciliation processes and exception management.

The rule catalogue describes intended source data guarantees to ensure downstream data product integrity, consistency, and quality.

## 2. Rule classifications

| Classification | Description | Example |
|---|---|---|
| Structural | Validity of record structure and attributes | Mandatory identifier is present |
| Referential | Validity of relationships between entities | Order references an existing customer |
| Temporal | Validity of business dates and effective intervals | Order does not precede customer creation |
| Financial | Correctness of monetary representation and arithmetic | Captured amount equals confirmed order total |
| Quantitative | Correctness of operational quantities | Returned quantity does not exceed shipped quantity |
| Lifecycle | Validity of operational state and transitions | Consumed reservation has a consumption date |
| Reconciliation | Consistency between independently owned datasets | Dispatch units equal outbound shipment units |
| Semantic | Correct interpretation of business concepts | Reservation does not change physical stock |

### 2.1 Severity

The following severity model is proposed for downstream validation.

| Severity | Meaning | Expected handling |
|---|---|---|
| CRITICAL | Compromises material financial, inventory or dataset integrity | Block affected publication or processing scope |
| ERROR | Invalid record or business relationship | Reject, quarantine or fail according to contract |
| WARNING | Potential anomaly requiring investigation | Record and monitor; processing may continue |
| INFO | Valid operational observation | Retain for analysis and monitoring |


### 2.2 Validation scope

Rules may operate at different levels:

| Scope | Description |
|---|---|
| Record | Validation of a single record |
| Entity | Validation across records belonging to one dataset |
| Relationship | Validation between related entities |
| Aggregate | Validation of counts, quantities or financial totals |
| Temporal | Validation across effective periods or event history |
| Estate | Validation across multiple operational systems |



## 3. General source invariants

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| GEN-001 | Mandatory identifiers | Record | Required source identifiers are present and non-empty | ERROR |
| GEN-002 | Entity identity | Entity | Logical primary identifiers are unique within their defined source scope | CRITICAL |
| GEN-003 | Referential integrity | Relationship | Mandatory references resolve to the correct parent entity when all relevant data is available | ERROR |
| GEN-004 | Controlled vocabulary | Record | Enumerated values belong to the corresponding entity-specific domain | ERROR |
| GEN-005 | Nullability | Record | Null values occur only where permitted by the model | ERROR |
| GEN-006 | Grain integrity | Entity | Records conform to the documented entity grain | CRITICAL |
| GEN-007 | Market validity | Record | Market codes belong to the configured simulation markets | ERROR |
| GEN-008 | Contextual consistency | Relationship | Shared market, product and other contextual attributes agree where required by the relationship | ERROR |
| GEN-009 | Source ownership | Semantic | Attributes and operational events are interpreted according to the owning source system | ERROR |
| GEN-010 | Source visibility | Estate | Simulator-internal demand-profile records are excluded from normal operational exports | CRITICAL |
| GEN-011 | Determinism | Estate | Identical supported generation inputs and execution environment reproduce equivalent source data | ERROR |
| GEN-012 | Baseline integrity | Estate | Unintentional integrity violations are absent from the clean baseline | CRITICAL |

## 4. Temporal invariants

Temporal relationships will be evaluated using the business meaning of the relevant dates.

The general effective interval temporal convention is inclusive start and exclusive end:

`valid_from <= observation_time < valid_to`

An absent end boundary may represent an open ended interval bound where permitted.

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| TMP-001 | Valid effective interval | Record | End boundary occurs after start boundary when an end boundary exists | ERROR |
| TMP-002 | Effective interval exclusivity | Temporal | Mutually exclusive versions do not overlap within the same business-key scope | CRITICAL |
| TMP-003 | Parent existence at event time | Relationship | A dependent event does not precede the relevant parent entity's existence | ERROR |
| TMP-004 | Lifecycle validity | Temporal | Events requiring an active entity occur within its permitted active period | ERROR |
| TMP-005 | Causal ordering | Temporal | Dependent events do not precede their causal predecessor | ERROR |
| TMP-006 | Historical entities | Record | Entity creation before the simulation activity window is permitted | INFO |
| TMP-007 | Post-window consequences | Temporal | Consequences of valid earlier events may occur after the activity window | INFO |
| TMP-008 | Observation cutoff | Temporal | Point-in-time datasets exclude information not observable by the declared cutoff | CRITICAL |
| TMP-009 | Temporal precision | Record | Dates and timestamps retain their original source precision | ERROR |
| TMP-010 | Business-time interpretation | Semantic | Business event time is not substituted with extraction, ingestion or processing time | ERROR |


## 5. Financial invariants

A monetary value must be interpreted together with its currency.

Financial calculations use decimal arithmetic rather than binary floating point arithmetic.

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| FIN-001 | Currency presence | Record | Monetary records have an explicit or unambiguously inherited currency | ERROR |
| FIN-002 | Currency validity | Record | Currency belongs to the applicable supported currency domain | ERROR |
| FIN-003 | Decimal representation | Structural | Monetary values retain their required decimal precision | ERROR |
| FIN-004 | Positive commercial price | Record | Active commercial prices are positive | ERROR |
| FIN-005 | Monetary context | Relationship | Related financial records use consistent currencies where required by their source contract | CRITICAL |
| FIN-006 | Historical price preservation | Temporal | Recorded transaction prices are not retrospectively replaced by newer product prices | CRITICAL |
| FIN-007 | Cross-currency aggregation | Semantic | Values in different currencies are not directly aggregated as a single monetary measure | CRITICAL |
| FIN-008 | Explicit FX conversion | Semantic | Reporting-currency amounts use an identifiable dated FX policy | CRITICAL |
| FIN-009 | Original currency preservation | Semantic | Currency conversion does not overwrite the original transaction amount or denomination | CRITICAL |


## 6. Product, assortment and pricing

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| PIM-001 | Product identity | Entity | Product identifiers are unique | CRITICAL |
| PIM-002 | SKU identity | Entity | SKUs satisfy their implemented uniqueness and identity constraints | ERROR |
| PIM-003 | Product lifecycle | Temporal | Product lifecycle dates form a valid sequence | ERROR |
| AST-001 | Product reference | Relationship | Every assortment references an existing product | ERROR |
| AST-002 | Market-assortment identity | Entity | Assortments satisfy product-market uniqueness constraints | ERROR |
| AST-003 | Assortment lifecycle | Temporal | Assortment activity is compatible with the associated product lifecycle | ERROR |
| AST-004 | Product consistency | Relationship | Assortment product identifiers and SKU attributes agree with PIM | ERROR |
| PRC-001 | Assortment reference | Relationship | Every price references an existing assortment | ERROR |
| PRC-002 | Price-period validity | Temporal | Every price version has a valid effective interval | ERROR |
| PRC-003 | Price-period overlap | Temporal | Competing active price versions do not overlap for the same pricing scope | CRITICAL |
| PRC-004 | Price coverage | Temporal | Eligible transactions resolve to an applicable price version | CRITICAL |
| PRC-005 | Price currency | Relationship | Price denomination agrees with its applicable market and commercial context | ERROR |
| PRC-006 | Price amount | Record | Unit price is positive and preserves decimal precision | ERROR |
| PRC-007 | Transaction-price lineage | Relationship | Order-item price references agree with the product, assortment and transaction-time price | CRITICAL |


## 7. Store, customer and loyalty

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| STR-001 | Store identity | Entity | Store identifiers and business codes satisfy their uniqueness constraints | ERROR |
| STR-002 | Store market | Record | Store belongs to a valid configured market | ERROR |
| STR-003 | Store lifecycle | Temporal | Opening and closing dates form a valid lifecycle | ERROR |
| CRM-001 | Customer identity | Entity | Customer identifiers are unique | CRITICAL |
| CRM-002 | Customer lifecycle | Temporal | Deactivation does not precede creation | ERROR |
| CRM-003 | Customer contactability | Record | Customer satisfies the configured minimum contact-information requirement | ERROR |
| CRM-004 | Optional contact attributes | Record | Permitted missing email or phone values are not automatically treated as defects | INFO |
| LOY-001 | Customer reference | Relationship | Every loyalty membership references an existing customer | ERROR |
| LOY-002 | Membership lifecycle | Temporal | Membership dates are compatible with the customer lifecycle | ERROR |
| LOY-003 | Membership identity | Entity | Membership uniqueness conforms to the implemented model | ERROR |
| LOY-004 | Membership tier | Record | Membership tier belongs to the supported vocabulary | ERROR |


## 8. Supplier and procurement

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| SUP-001 | Supplier identity | Entity | Supplier identifiers are unique | ERROR |
| SUP-002 | Supplier capability | Relationship | Capability records reference valid suppliers and supported product scope | ERROR |
| SRC-001 | Sourcing lineage | Relationship | Sourcing agreement references an existing supplier and assortment | ERROR |
| SRC-002 | Capability compatibility | Relationship | Sourced products are compatible with supplier capabilities | ERROR |
| SRC-003 | Sourcing role | Record | Sourcing role belongs to the supported domain | ERROR |
| SRC-004 | Primary sourcing | Entity | Each eligible assortment has its required primary sourcing relationship | ERROR |
| SRC-005 | Lead time | Record | Lead time satisfies the configured positive-duration constraints | ERROR |
| PO-001 | Purchase-order identity | Entity | Purchase-order identifiers are unique | CRITICAL |
| PO-002 | Header-line integrity | Relationship | Every purchase-order line references an existing purchase order | CRITICAL |
| PO-003 | Order-line coverage | Relationship | Every generated purchase order contains at least one line | ERROR |
| PO-004 | Sourcing compatibility | Relationship | Purchase-order line references a compatible sourcing agreement | ERROR |
| PO-005 | Ordered quantity | Record | Ordered quantity is positive | ERROR |
| PO-006 | Procurement chronology | Temporal | Expected receipt does not precede purchase-order creation | ERROR |
| PO-007 | Fulfilment coverage | Relationship | Every completed baseline PO line has one fulfilment-outcome record | ERROR |
| PO-008 | Shipment quantity | Aggregate | Total quantity shipped against a PO line does not exceed its ordered quantity | CRITICAL |
| PO-009 | Cancellation consistency | Lifecycle | Cancelled PO-line fulfilment does not produce inconsistent positive shipment quantities | ERROR |
| PO-010 | Receipt lineage | Relationship | Goods receipt references a valid supplier shipment and procurement lineage | ERROR |
| PO-011 | Receipt quantity | Relationship | Received quantity reconciles to the associated shipment under the current model | CRITICAL |
| PO-012 | Receipt chronology | Temporal | Receipt does not precede supplier dispatch | ERROR |
| PO-013 | Supplier outcome validity | Lifecycle | Fulfilment outcome agrees with the recorded quantities and dates | ERROR |

Late deliveries, split shipments, cancellations and short shipments are supported operational outcomes. Their occurrence alone is not a data quality failure, a failure in these cases would have to be substantiated with the accumulation of more lesser failures or ones of significant criticality.

## 9. Warehouse topology and routing

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| WMS-001 | Warehouse identity | Entity | Warehouse identifiers are unique | ERROR |
| WMS-002 | Location ownership | Relationship | Every inventory location belongs to an existing warehouse | ERROR |
| WMS-003 | Location topology | Entity | Each baseline warehouse contains its required logical location classes | ERROR |
| WMS-004 | Location capabilities | Record | Receipt, dispatch and sellability attributes agree with location semantics | ERROR |
| WMS-005 | Warehouse assortment | Relationship | Warehouse assortment references an existing warehouse and market assortment | ERROR |
| WMS-006 | Market compatibility | Relationship | Warehouse assortment is compatible with its market scope | ERROR |
| WMS-007 | Stocking interval | Temporal | Warehouse stocking intervals are valid | ERROR |
| WMS-008 | Route coverage | Relationship | Every generated PO line has one inbound receipt route | ERROR |
| WMS-009 | Route compatibility | Relationship | Inbound route points to the appropriate warehouse assortment and receiving location | ERROR |
| WMS-010 | Opening-stock coverage | Entity | Every warehouse assortment active at simulation start receives its required opening inventory | ERROR |

### 9.1 Location capability matrix

| Location type | Sellable | Direct receipt | Direct dispatch |
|---|---:|---:|---:|
| `RECEIVING` | No | Yes | No |
| `BULK_STORAGE` | Yes | No | No |
| `PICK_FACE` | Yes | No | Yes |
| `RETURNS` | No | No | No |
| `QUARANTINE` | No | No | No |

Physical stock and sellable stock are different measures. Physical stock referring to the stock present, and sellable stock being stock that is deemed of sufficient quality for distrubution (not quarantined or flagged at the operational source system level).

## 10. Physical inventory ledger

### 10.1 Movement semantics

| Movement type | Location | Quantity sign | Business meaning |
|---|---|---:|---|
| `OPENING_BALANCE` | BULK_STORAGE | Positive | Initial stock position |
| `RECEIPT` | RECEIVING | Positive | Physical receipt from supplier |
| `PUTAWAY_OUT` | RECEIVING | Negative | Removal from receiving location |
| `PUTAWAY_IN` | BULK_STORAGE | Positive | Addition to storage |
| `PICK_OUT` | BULK_STORAGE | Negative | Removal from storage for picking |
| `PICK_IN` | PICK_FACE | Positive | Addition to dispatchable location |
| `DISPATCH` | PICK_FACE | Negative | Physical shipment from warehouse |
| `RETURN_RECEIPT` | RETURNS | Positive | Receipt of customer-returned inventory |
| `RETURN_TRANSFER_OUT` | RETURNS | Negative | Removal from returns location for disposition |
| `RESTOCK_IN` | BULK_STORAGE | Positive | Returned stock restored to sellable inventory |
| `QUARANTINE_IN` | QUARANTINE | Positive | Returned stock moved into isolation |
| `WRITE_OFF` | RETURNS | Negative | Returned stock removed from physical inventory |

### 10.2 Accounting equations

Physical inventory at an observation date is the cumulative sum of signed movements within the relevant inventory scope.

`physical_on_hand(t) = SUM(quantity_delta WHERE event_date <= t)`

At the complete warehouse network level:

`physical_on_hand = opening_stock + receipts - dispatches + return_receipts - write_offs`

Internal transfers cancel when aggregated across their complete movement groups.

A movement group's internal-transfer components may not cancel at an intermediate observation time if the transfer is incomplete at that time.

Reservations are excluded from the physical inventory equation.

### 10.3 Ledger rules

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| INV-001 | Movement identity | Entity | Movement identifiers are unique | CRITICAL |
| INV-002 | Movement quantity | Record | Movement quantity is non-zero | ERROR |
| INV-003 | Movement sign | Record | Quantity sign agrees with movement type | CRITICAL |
| INV-004 | Movement location | Relationship | Movement references a valid compatible inventory location | ERROR |
| INV-005 | Inventory context | Relationship | Warehouse, assortment, product and location references are consistent | ERROR |
| INV-006 | Movement grouping | Entity | Movement-group membership and sequence follow the associated process semantics | ERROR |
| INV-007 | Source lineage | Relationship | Movement references the applicable originating business event or opening-balance source | ERROR |
| INV-008 | Internal-transfer conservation | Aggregate | Completed internal-transfer movements sum to zero | CRITICAL |
| INV-009 | Receipt accounting | Reconciliation | Supplier receipts reconcile to positive RECEIPT movement quantities | CRITICAL |
| INV-010 | Putaway accounting | Reconciliation | Completed putaway quantities reconcile to the associated receipt quantities | CRITICAL |
| INV-011 | Dispatch accounting | Reconciliation | Dispatch movement quantities reconcile to outbound shipments | CRITICAL |
| INV-012 | Return accounting | Reconciliation | Return-receipt movements reconcile to customer-return quantities | CRITICAL |
| INV-013 | Write-off accounting | Reconciliation | WRITE_OFF movements reconcile to write-off disposition quantities | CRITICAL |
| INV-014 | Physical balance | Aggregate | Physical inventory reconciles to the signed movement ledger | CRITICAL |
| INV-015 | Negative inventory | Temporal | Reconstructed physical balances do not become negative at the supported operational validation grain | CRITICAL |
| INV-016 | Reservation isolation | Semantic | Reservation creation does not itself generate physical stock movement | CRITICAL |
| INV-017 | Non-sellable stock | Semantic | Stock in non-sellable locations does not contribute to sellable inventory | CRITICAL |

INV-015 must respect the simulator's date-level and movement-sequence conventions. It must not assume an exact intraday chronology when the source only provides dates.

### 10.4 Process-level movement reconciliation

| Completed business process | Required movement pattern | Net physical effect |
|---|---|---:|
| Opening inventory | OPENING_BALANCE | +Q |
| Goods receipt and putaway | RECEIPT, PUTAWAY_OUT, PUTAWAY_IN | +Q |
| Outbound pick and dispatch | PICK_OUT, PICK_IN, DISPATCH | -Q |
| Customer-return receipt | RETURN_RECEIPT | +Q |
| Return restock | RETURN_TRANSFER_OUT, RESTOCK_IN | 0 |
| Return quarantine | RETURN_TRANSFER_OUT, QUARANTINE_IN | 0 |
| Return write-off | WRITE_OFF | -Q |
| Inventory reservation | No physical movement | 0 |

The ledger represents warehouse stock. It must not be interpreted as a complete enterprise inventory ledger covering all stock movements at the store level.

## 11. Order management

### 11.1 Financial arithmetic

For each order item:

`line_total = quantity × unit_price`

For each order:

`order_total = SUM(line_total for associated order items)`

The calculation reflects the current simplified source model. It does not include a comprehensive tax, discount or accounting engine.

### 11.2 Order rules

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| OMS-001 | Order identity | Entity | Order identifiers are unique | CRITICAL |
| OMS-002 | Customer reference | Relationship | Order references an existing customer | ERROR |
| OMS-003 | Customer eligibility | Temporal | Customer is eligible to transact on the order date | ERROR |
| OMS-004 | Order channel | Record | Channel belongs to the supported domain | ERROR |
| OMS-005 | Store-channel reference | Relationship | STORE order references an appropriate store | ERROR |
| OMS-006 | Store eligibility | Temporal | Referenced store is active on the transaction date | ERROR |
| OMS-007 | Order-item identity | Entity | Order-item identifiers are unique | CRITICAL |
| OMS-008 | Header-line coverage | Relationship | Every order contains at least one order item | ERROR |
| OMS-009 | Line sequence | Entity | Line numbers are unique within their parent order | ERROR |
| OMS-010 | Order-item reference | Relationship | Every order item references an existing order | CRITICAL |
| OMS-011 | Assortment eligibility | Temporal | Ordered assortment is valid for the market at transaction time | ERROR |
| OMS-012 | Ordered quantity | Record | Ordered quantity is positive | ERROR |
| OMS-013 | Unit-price integrity | Relationship | Recorded unit price agrees with the applicable referenced source price | CRITICAL |
| OMS-014 | Line arithmetic | Record | Line total equals quantity multiplied by unit price | CRITICAL |
| OMS-015 | Header arithmetic | Aggregate | Order total equals the sum of associated line totals | CRITICAL |
| OMS-016 | Cancellation state | Lifecycle | Cancellation attributes agree with order status | ERROR |
| OMS-017 | Cancellation chronology | Temporal | Cancellation does not precede order creation | ERROR |
| OMS-018 | Digital fulfilment eligibility | Semantic | Only confirmed WEB and MOBILE order items enter warehouse fulfilment | CRITICAL |

Cancelled orders remain valid operational records. Their financial and fulfilment treatment differs from confirmed orders.

## 12. Payments

Payment attempts must be evaluated at the payment attempt grain rather than assumed to be equivalent to orders.

Multiple attempts against one order are valid.

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| PAY-001 | Payment identity | Entity | Payment-attempt identifiers are unique | CRITICAL |
| PAY-002 | Order reference | Relationship | Every payment attempt references an existing order | ERROR |
| PAY-003 | Attempt sequence | Entity | Payment-attempt numbers are unique and valid within an order | ERROR |
| PAY-004 | Attempt amount | Relationship | Attempt amount agrees with the associated order amount under the current model | CRITICAL |
| PAY-005 | Payment denomination | Relationship | Payment currency agrees with order currency | CRITICAL |
| PAY-006 | Confirmed-order coverage | Reconciliation | Every confirmed baseline order has a captured payment | CRITICAL |
| PAY-007 | Capture uniqueness | Reconciliation | A confirmed order has exactly one captured payment | CRITICAL |
| PAY-008 | Cancelled-order coverage | Reconciliation | Every cancelled baseline order has its required voided payment | CRITICAL |
| PAY-009 | Void uniqueness | Reconciliation | A cancelled order has exactly one voided final attempt | CRITICAL |
| PAY-010 | Capture amount | Reconciliation | Captured amount equals confirmed order total | CRITICAL |
| PAY-011 | Capture eligibility | Lifecycle | Captured payments belong to confirmed orders under the baseline contract | CRITICAL |
| PAY-012 | Void eligibility | Lifecycle | Voided final attempts belong to cancelled orders under the baseline contract | ERROR |
| PAY-013 | Payment chronology | Temporal | Payment lifecycle timestamps follow their valid causal order | ERROR |
| PAY-014 | Status-timestamp consistency | Lifecycle | Capture, decline and void timestamps agree with the payment status | ERROR |
| PAY-015 | Decline attributes | Lifecycle | Decline-specific attributes agree with the payment outcome | ERROR |
| PAY-016 | Method applicability | Record | Card, wallet and bank attributes are populated according to payment method | ERROR |
| PAY-017 | Retry semantics | Semantic | Failed attempts do not create duplicate captured revenue | CRITICAL |

Operational payment failures are expected and have been modelled in the simulator. The invalid condition is inconsistent representation of the failure or its financial consequences rather than just an arbitary payment attempt failure.

## 13. Fulfilment, allocation and reservations

### 13.1 Quantity equations

For each fulfilment request:

`requested_quantity = allocated_quantity + unallocated_quantity`

For each request:

`allocated_quantity = SUM(associated allocation quantities)`

For each allocation in the completed baseline:

`allocated_quantity = reserved_quantity = shipped_quantity`

### 13.2 Fulfilment rules

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| FUL-001 | Request eligibility | Relationship | Request references an eligible confirmed digital order item | CRITICAL |
| FUL-002 | Request coverage | Reconciliation | Every eligible order item has its required fulfilment request | CRITICAL |
| FUL-003 | Request uniqueness | Entity | At most one request exists per eligible order item | ERROR |
| FUL-004 | Requested quantity | Relationship | Requested quantity equals the corresponding order-item quantity | CRITICAL |
| FUL-005 | Allocation arithmetic | Record | Allocated and unallocated quantities sum to requested quantity | CRITICAL |
| FUL-006 | Quantity bounds | Record | Allocated and unallocated quantities are non-negative | ERROR |
| FUL-007 | Allocation lineage | Relationship | Allocation references an existing compatible request | ERROR |
| FUL-008 | Allocation total | Aggregate | Allocation fragments sum to request-level allocated quantity | CRITICAL |
| FUL-009 | Allocation eligibility | Temporal | Allocated warehouse assortment is eligible on the allocation date | ERROR |
| FUL-010 | Inventory constraint | Temporal | Allocation does not exceed stock available under the simulator's allocation convention | CRITICAL |
| FUL-011 | Allocation status | Lifecycle | Request allocation status agrees with allocated and unallocated quantities | ERROR |
| RES-001 | Reservation coverage | Reconciliation | Every baseline allocation has its corresponding reservation | CRITICAL |
| RES-002 | Reservation uniqueness | Entity | One reservation exists per allocation in the current baseline | ERROR |
| RES-003 | Reservation quantity | Relationship | Reserved quantity equals associated allocated quantity | CRITICAL |
| RES-004 | Reservation chronology | Temporal | Reservation release or consumption does not precede creation | ERROR |
| RES-005 | Reservation lifecycle | Lifecycle | Status and lifecycle dates describe a consistent reservation state | ERROR |
| RES-006 | Physical separation | Semantic | Active reservations affect available-to-promise inventory without independently modifying physical stock | CRITICAL |
| SHP-001 | Shipment coverage | Reconciliation | Every reservation expected to complete outbound fulfilment has its corresponding shipment | CRITICAL |
| SHP-002 | Shipment uniqueness | Entity | One shipment exists per reservation in the completed baseline | ERROR |
| SHP-003 | Shipment quantity | Relationship | Shipped quantity equals associated reservation quantity in the current model | CRITICAL |
| SHP-004 | Shipment chronology | Temporal | Picking and dispatch occur in valid causal order | ERROR |
| SHP-005 | Reservation consumption | Lifecycle | Completed outbound fulfilment is represented by consistent consumed-reservation state | CRITICAL |
| SHP-006 | Outbound ledger accounting | Reconciliation | Physical dispatch movements reconcile to outbound shipment quantities | CRITICAL |

Unallocated or partially allocated requests remain valid operational demand records.

The absence of an allocation may indicate an inventory constraint rather than a missing data defect.

## 14. Returns and disposition

### 14.1 Quantity bounds

For each customer return:

`0 < returned_quantity <= shipped_quantity`

For each completed baseline return:

`disposition_quantity = returned_quantity`

### 14.2 Return rules

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| RET-001 | Shipment reference | Relationship | Every customer return references an existing outbound shipment | ERROR |
| RET-002 | Return uniqueness | Entity | At most one customer return exists per shipment under the current model | ERROR |
| RET-003 | Return quantity | Relationship | Returned quantity is positive and does not exceed shipped quantity | CRITICAL |
| RET-004 | Return chronology | Temporal | Return receipt does not precede outbound dispatch | ERROR |
| RET-005 | Return lineage | Relationship | Return order, item, assortment and warehouse references agree with shipment lineage | ERROR |
| RET-006 | Return reason | Record | Return reason belongs to the supported domain | ERROR |
| RET-007 | Receipt accounting | Reconciliation | Received-return quantity reconciles to RETURN_RECEIPT movements | CRITICAL |
| DSP-001 | Disposition coverage | Reconciliation | Every completed baseline return has a disposition | CRITICAL |
| DSP-002 | Disposition uniqueness | Entity | One disposition exists per return in the current model | ERROR |
| DSP-003 | Disposition quantity | Relationship | Disposition quantity equals returned quantity | CRITICAL |
| DSP-004 | Disposition chronology | Temporal | Disposition does not precede return receipt | ERROR |
| DSP-005 | Restock conservation | Reconciliation | Completed restock transfers preserve total physical inventory | CRITICAL |
| DSP-006 | Quarantine conservation | Reconciliation | Completed quarantine transfers preserve total physical inventory | CRITICAL |
| DSP-007 | Write-off accounting | Reconciliation | Write-off disposition reduces physical inventory by its disposition quantity | CRITICAL |
| DSP-008 | Destination semantics | Relationship | Disposition movement destinations agree with disposition type | ERROR |

A quarantined or written-off product represents a valid operational inventory outcome, not necessarily defective source data.

## 15. Refunds

### 15.1 Refund arithmetic

For each refund:

`refund_amount = original_order_item_unit_price × refunded_quantity`

For each captured payment:

`SUM(associated refund_amounts) <= captured_payment_amount`

Refunds are separate financial transactions. They do not erase or replace the original captured payment.

### 15.2 Refund rules

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| REF-001 | Return reference | Relationship | Every refund references a valid customer return | ERROR |
| REF-002 | Refund coverage | Reconciliation | Every completed baseline return has its corresponding refund | CRITICAL |
| REF-003 | Refund uniqueness | Entity | One refund exists per return in the current model | ERROR |
| REF-004 | Captured-payment reference | Relationship | Refund references a valid CAPTURED payment | CRITICAL |
| REF-005 | Payment ownership | Relationship | Referenced payment belongs to the corresponding original order | CRITICAL |
| REF-006 | Refund quantity | Relationship | Refunded quantity equals the entitled returned quantity | CRITICAL |
| REF-007 | Historical refund price | Financial | Refund uses the original recorded transaction price | CRITICAL |
| REF-008 | Refund arithmetic | Record | Refund amount equals original unit price multiplied by refunded quantity | CRITICAL |
| REF-009 | Currency consistency | Relationship | Refund denomination agrees with the original payment and transaction currency | CRITICAL |
| REF-010 | Cumulative refund limit | Aggregate | Total refunds against a payment do not exceed its captured amount | CRITICAL |
| REF-011 | Refund chronology | Temporal | Refund does not precede its required return and captured-payment events at the available source precision | ERROR |
| REF-012 | Financial state preservation | Semantic | Refund execution does not replace the original payment status with a synthetic refunded status | ERROR |

## 16. Availability

### 16.1 Availability equations

For an operationally supported market assortment:

`sellable_on_hand = SUM(physical balances in sellable locations)`

`available_to_promise = sellable_on_hand - active_reserved_quantity`

Where demand is positive:

`days_of_cover = available_to_promise / average_daily_units`

The current baseline rounds days of cover to two decimal places using the configured decimal rounding policy.

For assortments without an active supporting warehouse assortment, unavailable-state rules override ordinary ATP and days-of-cover calculations.

### 16.2 Reservation activity

A reservation is active at observation date `t` when:

- its reservation date is on or before `t`;
- it has not been released on or before `t`;
- it has not been consumed on or before `t`.

A future release or consumption must not remove a reservation from an earlier historical observation.

### 16.3 Status decision table

| Active warehouse count | ATP | Days of cover | Expected status |
|---:|---:|---|---|
| 0 | 0 | Null | `UNAVAILABLE` |
| Greater than 0 | 0 | Zero | `OUT_OF_STOCK` |
| Greater than 0 | Positive | Below low-stock threshold | `LOW_STOCK` |
| Greater than 0 | Positive | At or above low-stock threshold | `IN_STOCK` |

The default low-stock threshold in the current simulator is seven days of cover.

### 16.4 Availability rules

| Rule ID | Rule | Scope | Expected condition | Severity |
|---|---|---|---|---|
| AVL-001 | Snapshot identity | Entity | Snapshot identity is unique at the documented snapshot grain | ERROR |
| AVL-002 | Assortment coverage | Reconciliation | Every expected assortment receives its generated snapshot | ERROR |
| AVL-003 | Observation cutoff | Temporal | Only movements and reservation effects observable by the snapshot date contribute to the snapshot | CRITICAL |
| AVL-004 | Active warehouse count | Temporal | Warehouse count reflects valid effective stocking relationships | ERROR |
| AVL-005 | Sellable stock | Aggregate | Sellable inventory excludes non-sellable locations | CRITICAL |
| AVL-006 | Reservation activity | Temporal | Reserved quantity includes only reservations active at the snapshot date | CRITICAL |
| AVL-007 | Reservation bounds | Aggregate | Active reserved quantity does not exceed the applicable sellable inventory under the current model | CRITICAL |
| AVL-008 | ATP arithmetic | Record | Supported-assortment ATP equals sellable inventory minus active reservations | CRITICAL |
| AVL-009 | Demand validity | Record | Average daily demand is positive | ERROR |
| AVL-010 | Days-of-cover arithmetic | Record | Days of cover follows the configured calculation and rounding policy | ERROR |
| AVL-011 | Unavailable state | Lifecycle | No active supporting warehouse results in UNAVAILABLE, zero ATP and null days of cover | ERROR |
| AVL-012 | Status consistency | Lifecycle | Availability status agrees with warehouse support, ATP and configured threshold | ERROR |
| AVL-013 | Derived-state isolation | Semantic | Availability snapshots do not generate physical inventory movements | ERROR |

An unsupported assortment may retain physical inventory from an earlier stocking period. Physical presence alone does not imply operational availability.

## 17. Implemented estate-wide reconciliation

The canonical estate reconciliation is implemented in:

`src/mercatura/source/estate/reconciliation.py`

The following identifiers correspond to the implemented complete estate reconciliation checks established during the initial development phase.

They are distinct from the documentation level rule identifiers defined above.

| Implemented check | Logical rule reference | Validation |
|---|---|---|
| `PAYMENT_CAPTURE_COVERAGE` | PAY-006, PAY-011 | Confirmed orders and captured-payment order coverage agree |
| `PAYMENT_VOID_COVERAGE` | PAY-008, PAY-012 | Cancelled orders and voided-payment order coverage agree |
| `PAYMENT_SINGLE_CAPTURE` | PAY-007 | Confirmed orders do not have duplicate captures |
| `PAYMENT_SINGLE_VOID` | PAY-009 | Cancelled orders do not have duplicate final voids |
| `PAYMENT_CAPTURE_AMOUNT` | PAY-010 | Captured amounts equal confirmed order totals |
| `FULFILMENT_REQUEST_COVERAGE` | FUL-001, FUL-002 | Requests cover eligible digital order items |
| `FULFILMENT_REQUEST_UNIQUENESS` | FUL-003 | Eligible order items do not have duplicate requests |
| `FULFILMENT_REQUEST_QUANTITY` | FUL-004 | Requested quantities equal OMS quantities |
| `FULFILMENT_REQUEST_ARITHMETIC` | FUL-005 | Requested quantities reconcile to allocated and unallocated quantities |
| `ALLOCATION_REQUEST_REFERENCES` | FUL-007 | Allocations reference valid requests |
| `ALLOCATION_QUANTITY` | FUL-008 | Allocation fragments reconcile to request totals |
| `RESERVATION_COVERAGE` | RES-001 | Allocations and reservations have matching coverage |
| `RESERVATION_UNIQUENESS` | RES-002 | Allocations have unique reservations |
| `RESERVATION_QUANTITY` | RES-003 | Reserved quantities reconcile to allocated quantities |
| `SHIPMENT_COVERAGE` | SHP-001 | Completed baseline reservations have shipments |
| `SHIPMENT_UNIQUENESS` | SHP-002 | Reservations do not have duplicate shipments |
| `SHIPMENT_QUANTITY` | SHP-003 | Shipped quantities reconcile to reserved quantities |
| `RETURN_SHIPMENT_REFERENCES` | RET-001 | Returns reference valid shipments |
| `RETURN_UNIQUENESS` | RET-002 | Shipments do not have duplicate returns |
| `RETURN_QUANTITY` | RET-003 | Returned quantities remain within shipped quantities |
| `DISPOSITION_COVERAGE` | DSP-001 | Returns have corresponding dispositions |
| `DISPOSITION_UNIQUENESS` | DSP-002 | Returns do not have duplicate dispositions |
| `DISPOSITION_QUANTITY` | DSP-003 | Disposition quantities reconcile to returned quantities |
| `REFUND_COVERAGE` | REF-002 | Returns have corresponding refunds |
| `REFUND_UNIQUENESS` | REF-003 | Returns do not have duplicate refunds |
| `REFUND_QUANTITY` | REF-006 | Refunded quantities reconcile to returned quantities |
| `REFUND_CAPTURE_REFERENCE` | REF-004 | Refunds reference captured payments |
| `REFUND_CAPTURE_LIMIT` | REF-010 | Cumulative refunds do not exceed captured amounts |
| `INVENTORY_DISPATCH_UNITS` | INV-011, SHP-006 | Dispatch units reconcile to shipment units |
| `INVENTORY_RETURN_UNITS` | INV-012, RET-007 | Return-receipt units reconcile to returned units |
| `INVENTORY_WRITE_OFF_UNITS` | INV-013, DSP-007 | Write-off movements reconcile to write-off dispositions |

A successful estate build requires the implemented reconciliation report to pass.

The wider logical catalogue also includes requirements enforced by individual source validators and requirements intended for downstream implementation.

Passing the complete estate report does not independently demonstrate that every logical rule in this document has been evaluated.

## 18. Data defects versus business exceptions

A valid representation of an undesirable operational event must not automatically be classified as invalid data.

| Scenario | Classification | Explanation |
|---|---|---|
| Payment declined | Valid business outcome | Payment processing can fail |
| Several payment attempts | Valid business outcome | Customers may retry payment |
| Multiple captured payments for one baseline order | Data defect | Violates the payment contract |
| Cancelled order | Valid business outcome | Orders may be cancelled |
| Captured payment against a cancelled baseline order | Data defect | Violates the current payment lifecycle |
| Late supplier shipment | Business exception | Delivery performance issue |
| Short supplier shipment | Business exception | Supplier fulfilment issue |
| Shipped quantity exceeding ordered quantity | Data defect | Violates the current procurement contract |
| No allocation available | Business exception | Operational inventory shortage |
| Allocation exceeding available inventory | Data defect | Violates allocation integrity |
| Product out of stock | Business exception | Valid stock-risk state |
| Negative physical inventory | Data defect | Violates the clean ledger baseline |
| Customer returns damaged item | Valid business outcome | Expected reverse-logistics event |
| Returned quantity exceeds shipped quantity | Data defect | Violates return integrity |
| Refund exceeds captured payment | Data defect | Violates financial integrity |
| Customer has no loyalty membership | Valid business state | Loyalty participation is optional |
| Customer has permitted missing contact field | Valid business state | Source model allows optional contact attributes |
| Customer missing mandatory identity | Data defect | Violates structural integrity |
| Non-English customer name | Valid source representation | International text is expected |
| Corrupted or lost Unicode content | Data defect | Violates source preservation |
| Exchange-rate movement | Valid external economic event | Currency values change over time |
| Undated or ambiguous FX conversion | Data defect | Reporting amount cannot be reliably reproduced |

Business exceptions may be important analytical signals. Rejecting these records would remove valuable information from the platform.

## 19. Reconciliation scope and completeness

Complete estate reconciliation currently evaluates the completed generated world.

Incremental and point-in-time extracts may legitimately contain incomplete relationships.

| Relationship | Completed baseline expectation | Point-in-time interpretation |
|---|---|---|
| Purchase order to goods receipt | Completed outcomes reconcile | Receipt may not yet have occurred |
| Allocation to shipment | Completed reservations have shipments | Reservation may still be awaiting dispatch |
| Return to disposition | One disposition per completed return | Return may still await inspection |
| Return to refund | One refund per completed return | Financial processing may still be pending |
| Receipt to putaway | Completed movements reconcile | Stock may temporarily remain in receiving |
| Order to final payment | Completed payment outcome reconciles | Payment processing may still be in progress |

A downstream reconciliation engine must therefore distinguish:

- invalid relationships
- incomplete operational processes
- missing source deliveries
- late arriving records
- temporarily unresolved references

Completeness expectations will be evaluated against the relevant extraction scope, business observation time and source freshness requirements.

Whole estate aggregate equality is insufficient on its own. Compensating errors can produce correct totals while individual records remain incorrect.

Where practical, downstream reconciliation should validate at multiple grains:

| Grain | Purpose |
|---|---|
| Record | Identify individual defects |
| Business transaction | Reconcile related operational events |
| Product and location | Detect inventory inconsistencies |
| Market and currency | Reconcile local financial activity |
| Source entity | Detect missing or duplicated records |
| Extract or batch | Verify delivery completeness |
| Estate | Verify overall cross-system consistency |

## 20. Downstream data quality implementation

The documented rules should become inputs to the future automated data quality framework.

A machine readable rule definition may eventually contain:

| Attribute | Purpose |
|---|---|
| `rule_id` | Stable rule identifier |
| `description` | Human-readable business requirement |
| `dataset` | Primary validation target |
| `related_datasets` | Required supporting datasets |
| `rule_type` | Structural, referential, financial or other classification |
| `validation_scope` | Record, entity, relationship, aggregate or temporal |
| `severity` | Business impact of failure |
| `expression` | Executable validation logic or function reference |
| `threshold` | Permitted tolerance where applicable |
| `effective_from` | Rule activation date |
| `rule_version` | Version of validation semantics |
| `failure_action` | Reject, quarantine, alert or block publication |
| `owner` | Responsible technical or business owner |
| `enabled` | Whether the rule is active |

A candidate configuration could take the following form:

```yaml
rule_id: OMS-014
description: Order item line total must reconcile
dataset: oms.order_items
rule_type: financial
validation_scope: record
severity: critical
assertion:
  expression: "line_total = quantity * unit_price"
failure_action: block_affected_publication
rule_version: 1
enabled: true
```

This is a proposed metadata representation, the exact expressions, tolerances and enforcement mechanisms will be established when the data quality framework is built.

## 21. Validation evidence

A validation result will eventually contain sufficient information to establish what was evaluated, against which data and with what outcome.

Candidate result attributes include:

| Attribute | Purpose |
|---|---|
| `validation_run_id` | Identifies the validation execution |
| `rule_id` | Identifies the applied rule |
| `rule_version` | Identifies the validation semantics |
| `dataset` | Dataset evaluated |
| `extract_id` | Relevant upstream delivery |
| `evaluated_at` | Validation execution timestamp |
| `evaluated_count` | Number of records or groups evaluated |
| `passed_count` | Number satisfying the requirement |
| `failed_count` | Number violating the requirement |
| `not_evaluated_count` | Number lacking required evaluation context |
| `observed_value` | Observed aggregate or measured condition |
| `expected_value` | Expected condition where applicable |
| `status` | Validation outcome |
| `severity` | Applicable failure severity |
| `exception_reference` | Link to detailed failure evidence |
| `code_version` | Transformation or validation implementation version |


## 22. Rule maintenance

The rule catalogue is expected to evolve alongside source contracts and implementation.

- Rule identifiers should remain stable.
- Material changes to rule semantics should be versioned.
- Retired rules should remain traceable.
- Severity and enforcement changes should be deliberate.
- Every critical implemented rule should have positive and negative test coverage.
- Business exceptions should not be converted into data defects without an explicit change in business requirements.
- Point-in-time validation must respect source completeness and observation boundaries.

Rule definitions is aimed to ultimately be maintained in machine readable contracts or quality configurations, with supporting documentation where practical.

## 23. Known validation boundaries

| Boundary | Implication |
|---|---|
| Synthetic baseline | Passing validation does not prove real-world statistical representativeness |
| Completed-world reconciliation | Exact coverage rules may not apply to incomplete extracts |
| Date-level inventory events | Exact intraday ordering is not always reconstructible |
| Simplified financial model | Tax, discounts, settlement and statutory accounting are not comprehensively reconciled |
| Warehouse-only physical ledger | Store stock and in-store inventory consumption are outside the ledger boundary |
| No external FX dataset | Enterprise reporting-currency reconciliation is deferred |
| No full CDC implementation | Change-event ordering and deletion semantics require later contracts |
| Aggregate reconciliation | Matching totals alone cannot establish individual-record correctness |
| Documentation-level rules | Not every rule listed here has a dedicated implemented validator |
