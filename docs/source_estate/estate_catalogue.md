# Mercatura Source Estate — Model Catalogue



## 1. Purpose and scope

This document provides the logical catalogue of entities within the Mercatura operational source estate. It defines entity ownership, grain, identifiers, significant attributes, relationships and data classification.

It serves as a reference for source discovery, ingestion contract development, entity conformance, dimensional modelling and cross-system reconciliation.

The catalogue describes the simulated operational models rather than downstream analytical tables. 

Physical schemas will eventually be represented in machine readable contracts rather than maintained manually in multiple Markdown documents as to avoid potential documentation drift, especially with schema evolution being a considerable factor.

## 2. Entity catalogue

| Domain | Entity | Export dataset | Grain | Logical identifier | Key attributes and concepts | Principal relationships | Classification |
|---|---|---|---|---|---|---|---|
| STORE | `Store` | `stores` | One physical retail store | `store_id` | Store code, market, geography, store characteristics, lifecycle dates | Market; Order | Master |
| PIM | `Product` | `products` | One global product | `product_id` | SKU, product description, department, category, product lifecycle | ProductMarketAssortment; SupplierCapability; OrderItem | Master |
| ASSORTMENT | `ProductMarketAssortment` | `assortments` | One product-market ranging relationship | `assortment_id` | Product, SKU, market, assortment lifecycle | Product; ProductPrice; SourcingAgreement; WarehouseAssortment; OrderItem | Relationship |
| PRICING | `ProductPrice` | `prices` | One effective price version per market assortment | `price_id` | Assortment, product, market, currency, unit price, effective dates | ProductMarketAssortment; OrderItem | Temporal reference |
| SIMULATION | `DemandProfile` | Not exported | One latent demand profile per market assortment | `assortment_id` | `assortment_id`, `product_id`, `sku`, `market_code`, department, `average_daily_units`, volatility, `seasonality_strength` | ProductMarketAssortment; Procurement; OMS; WarehouseAssortment; AvailabilitySnapshot | Internal simulator state |
| SUPPLIER | `Supplier` | `suppliers` | One supplier organisation | `supplier_id` | Supplier identity, origin, organisational characteristics | SupplierCapability; SourcingAgreement; PurchaseOrder | Master |
| SUPPLIER | `SupplierCapability` | `supplier_capabilities` | One supplier capability relationship | `cabability_id` | Supplier, supported product scope or category | Supplier; Product; SourcingAgreement | Relationship |
| PROCUREMENT | `SourcingAgreement` | `sourcing_agreements` | One commercial sourcing relationship between a supplier and assortment | `sourcing_id` | Supplier, assortment, sourcing role, lead time, commercial terms | Supplier; SupplierCapability; ProductMarketAssortment; PurchaseOrderLine | Temporal relationship |
| PROCUREMENT | `PurchaseOrder` | `purchase_orders` | One procurement order | `purchase_order_id` | Supplier, market, currency, order date, procurement details | Supplier; PurchaseOrderLine | Transaction header |
| PROCUREMENT | `PurchaseOrderLine` | `purchase_order_lines` | One line within a purchase order | `purchase_order_line_id` | Purchase order, assortment, sourcing agreement, ordered quantity, unit cost, expected receipt | PurchaseOrder; SourcingAgreement; PurchaseOrderLineFulfilment; InboundReceiptRoute | Transaction line |
| PROCUREMENT | `PurchaseOrderLineFulfilment` | `purchase_order_line_fulfilments` | One fulfilment outcome per purchase-order line | `fulfilment_id` | Ordered quantity, fulfilled quantity, fulfilment outcome, delivery performance | PurchaseOrderLine; SupplierShipment | Lifecycle state |
| PROCUREMENT | `SupplierShipment` | `supplier_shipments` | One inbound supplier shipment | `shipment_id` | Purchase-order lineage, supplier, shipped quantity, shipment timing | PurchaseOrderLine; PurchaseOrderLineFulfilment; GoodsReceipt | Transaction |
| PROCUREMENT | `GoodsReceipt` | `goods_receipts` | One received supplier shipment in the current baseline | `goods_receipt_id` | Shipment lineage, received quantity, receipt date, procurement references | SupplierShipment; InboundReceiptRoute; InventoryMovement | Event |
| WMS | `Warehouse` | `warehouses` | One warehouse facility | `warehouse_id` | Warehouse code, market, geography, facility characteristics | InventoryLocation; WarehouseAssortment; InboundReceiptRoute | Master |
| WMS | `InventoryLocation` | `inventory_locations` | One logical inventory location within a warehouse | `inventory_location_id` | Warehouse, location type, sellability, receipt capability, dispatch capability | Warehouse; InventoryMovement | Master |
| WMS | `WarehouseAssortment` | `warehouse_assortments` | One warehouse-market-assortment stocking relationship | `warehouse_assortment_id` | Warehouse, assortment, product, SKU, stocking priority, `stocked_from`, `stocked_to` | Warehouse; ProductMarketAssortment; InboundReceiptRoute; FulfilmentAllocation; AvailabilitySnapshot | Temporal relationship |
| WMS | `InboundReceiptRoute` | `inbound_receipt_routes` | One inbound warehouse route per purchase-order line | `route_id` | Purchase-order lineage, warehouse destination, warehouse assortment, receiving location | PurchaseOrderLine; WarehouseAssortment; InventoryLocation; GoodsReceipt | Relationship |
| WMS | `InventoryMovement` | `inventory_movements` | One physical inventory movement at one location | `movement_id` | `movement_group_id`, `movement_sequence`, `event_date`, warehouse, location, assortment, movement type, quantity delta, movement source | InventoryLocation; WarehouseAssortment; GoodsReceipt; OutboundShipment; CustomerReturn; ReturnDisposition | Ledger event |
| CRM | `Customer` | `customers` | One customer identity | `customer_id` | Customer identity, native-language name, market, contact information, lifecycle dates | LoyaltyMembership; Order | Master |
| LOYALTY | `LoyaltyMembership` | `loyalty_memberships` | One customer loyalty membership | `membership_id` | Customer, membership tier, membership lifecycle | Customer | Lifecycle state |
| OMS | `Order` | `orders` | One customer order | `order_id` | `order_number`, `customer_id`, `market_code`, `currency`, `channel`, `store_id`, `store_code`, `order_date`, `order_status`, `cancelled_at`, `order_total` | Customer; Store; OrderItem; PaymentAttempt | Transaction header |
| OMS | `OrderItem` | `order_items` | One line within a customer order | `order_item_id` | `order_id`, `line_number`, `assortment_id`, `product_id`, `sku`, `price_id`, `quantity`, `unit_price`, `line_total` | Order; Product; ProductMarketAssortment; ProductPrice; FulfilmentRequest | Transaction line |
| PAYMENTS | `PaymentAttempt` | `payment_attempts` | One attempted payment transaction | `payment_id` | Payment and processor references, `order_id`, `attempt_number`, `market_code`, `currency`, `amount`, payment method, processor, card attributes, wallet provider, bank rail, payment token, entry mode, authentication result, payment status, decline details, lifecycle timestamps | Order; Refund | Financial transaction |
| FULFILMENT | `FulfilmentRequest` | `fulfilment_requests` | One fulfilment request per eligible digital order line | `fulfilment_request_id` | Order and item lineage, market, channel, assortment, product, SKU, `requested_quantity`, `allocated_quantity`, `unallocated_quantity`, `allocation_status`, `allocation_date` | Order; OrderItem; ProductMarketAssortment; FulfilmentAllocation | Lifecycle state |
| FULFILMENT | `FulfilmentAllocation` | `fulfilment_allocations` | One warehouse allocation fragment | `allocation_id` | `fulfilment_request_id`, order and item lineage, `allocation_sequence`, market, warehouse assortment, warehouse, product, SKU, `allocated_quantity`, `allocation_date` | FulfilmentRequest; WarehouseAssortment; InventoryReservation | Relationship |
| FULFILMENT | `InventoryReservation` | `inventory_reservations` | One inventory reservation per allocation | `reservation_id` | Allocation and request lineage, order and item lineage, warehouse assortment, warehouse, product, SKU, `reserved_quantity`, `reservation_status`, `reserved_date`, `released_date`, `consumed_date` | FulfilmentAllocation; WarehouseAssortment; OutboundShipment; AvailabilitySnapshot | Lifecycle state |
| FULFILMENT | `OutboundShipment` | `outbound_shipments` | One dispatched inventory reservation | `shipment_id` | Reservation, allocation and request lineage, order and item lineage, warehouse assortment, warehouse, product, SKU, `shipped_quantity`, `picked_date`, `dispatched_date`, `shipment_status` | InventoryReservation; InventoryMovement; CustomerReturn | Transaction |
| RETURNS | `CustomerReturn` | `customer_returns` | One received customer return against an outbound shipment | `return_id` | Shipment, reservation, allocation and request lineage, order and item lineage, warehouse assortment, warehouse, product, SKU, `returned_quantity`, `return_reason`, `return_status`, `return_date` | OutboundShipment; InventoryMovement; ReturnDisposition; Refund | Transaction |
| RETURNS | `ReturnDisposition` | `return_dispositions` | One disposition decision per customer return | `disposition_id` | `return_id`, shipment and order lineage, warehouse assortment, warehouse, product, SKU, `disposition_quantity`, `disposition_type`, `disposition_date` | CustomerReturn; InventoryMovement | Event |
| PAYMENTS | `Refund` | `refunds` | One financial refund per received customer return | `refund_id` | `refund_reference`, `return_id`, `payment_id`, `payment_reference`, `order_id`, `order_item_id`, `market_code`, `currency`, `refunded_quantity`, `refund_amount`, `processor`, `refund_status`, `refund_date` | CustomerReturn; PaymentAttempt; Order; OrderItem | Financial transaction |
| AVAILABILITY | `AvailabilitySnapshot` | `availability_snapshots` | One market assortment per snapshot date | `snapshot_id` | `snapshot_date`, `market_code`, `assortment_id`, `product_id`, `sku`, `active_warehouse_count`, `sellable_on_hand`, `reserved_quantity`, `available_to_promise`, `average_daily_units`, `days_of_cover`, `availability_status` | ProductMarketAssortment; WarehouseAssortment; InventoryMovement; InventoryReservation | Snapshot |

## 3. Data classification

The classifications in the catalogue describe the logical behaviour of each dataset. They inform downstream ingestion design but do not prescribe a specific extraction or CDC mechanism.

| Classification | Meaning | Downstream considerations |
|---|---|---|
| Master | Relatively persistent business entity | Identity management, attribute changes, SCD, lifecycle tracking |
| Relationship | Association between business entities | Referential integrity, composite uniqueness, cardinality |
| Temporal relationship | Association with business-effective dates | Interval validation, effective-date joins, historical conformance |
| Temporal reference | Time-dependent reference values | Point-in-time lookups, interval overlap detection |
| Transaction header | Business transaction at document level | Header-line reconciliation, lifecycle updates, deduplication |
| Transaction line | Individual component of a transaction | Parent integrity, quantity and financial reconciliation |
| Transaction | Operational business transaction | Business-key uniqueness, lifecycle tracking |
| Financial transaction | Monetary event or attempted monetary event | Currency preservation, decimal precision, financial reconciliation |
| Lifecycle state | Representation of an entity or process lifecycle | Status transitions, incremental updates, historical reconstruction |
| Event | Discrete operational occurrence | Event identity, event time, replay, late arrival |
| Ledger event | Signed movement contributing to an accumulated balance | Append-oriented processing, movement reconciliation, balance reconstruction |
| Snapshot | Derived state at a defined observation time | Snapshot-date uniqueness, point-in-time correctness, freshness |
| Internal simulator state | Synthetic information used to coordinate generation | Excluded from operational source ingestion |

## 4. Domain values

The following table consolidates significant controlled vocabularies.

| Entity | Attribute or concept | Supported values |
|---|---|---|
| SourcingAgreement | Supplier role | `PRIMARY`, `SECONDARY`, `BACKUP` |
| PurchaseOrderLineFulfilment | Fulfilment outcome | `ON_TIME_FULL`, `EARLY_FULL`, `LATE_FULL`, `SPLIT_FULL`, `SHORT_SHIPPED`, `CANCELLED` |
| InventoryLocation | Location type | `RECEIVING`, `BULK_STORAGE`, `PICK_FACE`, `RETURNS`, `QUARANTINE` |
| InventoryMovement | Movement type | `OPENING_BALANCE`, `RECEIPT`, `PUTAWAY_OUT`, `PUTAWAY_IN`, `PICK_OUT`, `PICK_IN`, `DISPATCH`, `RETURN_RECEIPT`, `RETURN_TRANSFER_OUT`, `RESTOCK_IN`, `QUARANTINE_IN`, `WRITE_OFF` |
| InventoryMovement | Movement source | `OPENING_BALANCE`, `GOODS_RECEIPT`, `FULFILMENT_SHIPMENT`, `CUSTOMER_RETURN`, `RETURN_DISPOSITION` |
| LoyaltyMembership | Membership tier | `STANDARD`, `SILVER`, `GOLD`, `PLATINUM` |
| Order | `channel` | `STORE`, `WEB`, `MOBILE` |
| Order | `order_status` | `CONFIRMED`, `CANCELLED` |
| PaymentAttempt | `payment_method` | `CARD`, `DIGITAL_WALLET`, `BANK_PAYMENT` |
| PaymentAttempt | `payment_status` | `DECLINED`, `CAPTURED`, `VOIDED` |
| PaymentAttempt | `card_network` | `VISA`, `MASTERCARD`, `AMEX`, `DISCOVER`, `JCB`, `UNIONPAY`, `MIR` |
| PaymentAttempt | `card_funding_type` | `DEBIT`, `CREDIT`, `PREPAID` |
| PaymentAttempt | `card_presence` | `CARD_PRESENT`, `CARD_NOT_PRESENT` |
| PaymentAttempt | `wallet_provider` | `APPLE_PAY`, `GOOGLE_PAY`, `PAYPAL`, `ALIPAY`, `WECHAT_PAY`, `MIR_PAY`, `PAYPAY`, `KAKAO_PAY`, `NAVER_PAY`, `SAMSUNG_PAY` |
| PaymentAttempt | `bank_payment_rail` | `FASTER_PAYMENTS`, `OPEN_BANKING`, `SEPA`, `ACH`, `LOCAL_BANK_TRANSFER`, `SBP`, `IDEAL`, `BLIK` |
| PaymentAttempt | `entry_mode` | `CONTACTLESS`, `CHIP_PIN`, `ECOMMERCE`, `WALLET_TOKEN`, `BANK_REDIRECT` |
| PaymentAttempt | `authentication_result` | `NOT_APPLICABLE`, `3DS_FRICTIONLESS`, `3DS_CHALLENGE`, `WALLET_AUTHENTICATED`, `BANK_AUTHENTICATED` |
| PaymentAttempt | `decline_type` | `SOFT`, `HARD` |
| PaymentAttempt | `decline_reason` | `INSUFFICIENT_FUNDS`, `DO_NOT_HONOUR`, `LIMIT_EXCEEDED`, `PROCESSOR_ERROR`, `EXPIRED_INSTRUMENT`, `INVALID_DETAILS`, `SUSPECTED_FRAUD` |
| InventoryReservation | `reservation_status` | `RESERVED`, `RELEASED`, `CONSUMED` |
| OutboundShipment | `shipment_status` | `DISPATCHED` |
| CustomerReturn | `return_status` | `RECEIVED` |
| CustomerReturn | `return_reason` | `UNWANTED`, `WRONG_SIZE_OR_FIT`, `DAMAGED`, `FAULTY`, `NOT_AS_DESCRIBED` |
| ReturnDisposition | `disposition_type` | `RESTOCK`, `QUARANTINE`, `WRITE_OFF` |
| Refund | `refund_status` | `REFUNDED` |
| AvailabilitySnapshot | `availability_status` | `IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`, `UNAVAILABLE` |

## 5. Relationship cardinalities



The multiplicity column specifies the permitted number of child records per parent.

| Parent entity | Child entity | Child multiplicity | Relationship semantics |
|---|---|---|---|
| Product | ProductMarketAssortment | 0..N | A global product may be ranged in multiple markets |
| ProductMarketAssortment | ProductPrice | 1..N | An assortment has one or more price versions |
| ProductMarketAssortment | DemandProfile | 1 | Exactly one internal demand profile per assortment |
| ProductMarketAssortment | SourcingAgreement | 1..N | Primary and optional alternative sourcing relationships |
| Supplier | SupplierCapability | 0..N | A supplier may support multiple capabilities |
| Supplier | SourcingAgreement | 0..N | A supplier may participate in multiple sourcing relationships |
| Supplier | PurchaseOrder | 0..N | Multiple procurement orders may be issued to one supplier |
| PurchaseOrder | PurchaseOrderLine | 1..N | An order contains one or more procurement lines |
| PurchaseOrderLine | PurchaseOrderLineFulfilment | 1 | One fulfilment outcome per line |
| PurchaseOrderLine | SupplierShipment | 0..N | Cancelled lines may have no shipment; split deliveries may create multiple shipments |
| SupplierShipment | GoodsReceipt | 1 | One receipt per shipment in the completed baseline |
| PurchaseOrderLine | InboundReceiptRoute | 1 | One destination route per procurement line |
| Warehouse | InventoryLocation | 5 | Five logical location types per warehouse in the current implementation |
| Warehouse | WarehouseAssortment | 0..N | A warehouse may stock multiple assortments |
| ProductMarketAssortment | WarehouseAssortment | 0..N | An assortment may be supported by multiple warehouses |
| InventoryLocation | InventoryMovement | 0..N | A location may receive multiple physical movements |
| Customer | LoyaltyMembership | 0..1 | Loyalty participation is optional |
| Customer | Order | 0..N | Customers may exist without purchasing |
| Store | Order | 0..N | Store-channel transactions reference a physical store |
| Order | OrderItem | 1..N | An order contains one or more items |
| Order | PaymentAttempt | 1..N | Payment retries may create multiple attempts |
| ProductPrice | OrderItem | 0..N | Multiple order lines may use the same historical price |
| OrderItem | FulfilmentRequest | 0..1 | Only confirmed digital order items are eligible |
| FulfilmentRequest | FulfilmentAllocation | 0..N | A request may be unallocated, allocated or split |
| FulfilmentAllocation | InventoryReservation | 1 | One reservation per allocation in the baseline |
| InventoryReservation | OutboundShipment | 1 | One shipment per reservation in the completed baseline |
| OutboundShipment | CustomerReturn | 0..1 | A shipment may produce a partial or full return |
| CustomerReturn | ReturnDisposition | 1 | One disposition per return in the completed baseline |
| CustomerReturn | Refund | 1 | One refund per return in the completed baseline |
| PaymentAttempt | Refund | 0..N | A captured payment may fund multiple return refunds |
| ProductMarketAssortment | AvailabilitySnapshot | 1 per snapshot date | One observation per assortment for each generated snapshot date |


## 6. Common attribute conventions

| Attribute pattern | Meaning | Modelling considerations |
|---|---|---|
| `*_id` | Source entity identifier | Preserve as an opaque identifier; do not infer business meaning from its format |
| `*_code` | Business or operational code | Preserve independently from technical identifiers |
| `*_reference` | Operational or external transaction reference | May require separate uniqueness rules |
| `market_code` | Commercial market | Must not be treated as a currency or language identifier |
| `currency` | Transaction or price denomination | Preserve alongside every monetary measure |
| `sku` | Stock keeping unit | Retain source representation and distinguish from product identifier |
| `*_date` | Business calendar date | Do not introduce timestamp precision that was absent in the source |
| `*_at` | Event or lifecycle timestamp | Preserve timezone semantics and source precision |
| `*_from`, `*_to` | Effective-period boundaries | Apply the documented inclusive-start, exclusive-end convention where applicable |
| `*_quantity` | Operational quantity | Interpret according to the entity grain and applicable unit |
| `*_amount`, `*_total`, `*_price` | Monetary measure | Use decimal arithmetic and explicit currency semantics |
| `*_status` | Operational lifecycle state | Validate against the relevant entity-specific vocabulary |
| `*_sequence` | Ordering within a parent or movement group | Do not assume global chronological ordering |
| `snapshot_date` | Business observation date | Distinguish from extraction and ingestion timestamps |

## 7. Downstream integration considerations

| Integration concern | Relevant entities | Required treatment |
|---|---|---|
| Historical pricing | ProductPrice, OrderItem | Resolve applicable price at transaction time; preserve recorded transaction price |
| Customer conformance | Customer, LoyaltyMembership, Order | Preserve CRM identity and distinguish membership from customer identity |
| Payment reconciliation | Order, PaymentAttempt | Separate failed attempts from captured revenue; prevent retry-related double counting |
| Refund reconciliation | CustomerReturn, Refund, PaymentAttempt | Preserve return and payment lineage; reconcile cumulative refunds |
| Procurement performance | PurchaseOrderLine, PurchaseOrderLineFulfilment, SupplierShipment, GoodsReceipt | Compare ordered, shipped and received quantities at appropriate grains |
| Inventory reconstruction | InventoryMovement, InventoryLocation | Accumulate signed movements by location, warehouse, assortment and observation time |
| Stock availability | InventoryReservation, InventoryMovement, AvailabilitySnapshot | Distinguish physical stock from active reservations and available-to-promise stock |
| Fulfilment performance | FulfilmentRequest, FulfilmentAllocation, InventoryReservation, OutboundShipment | Retain request-to-shipment lineage; account for split and unallocated demand |
| Multicurrency reporting | ProductPrice, PurchaseOrder, PurchaseOrderLine, Order, PaymentAttempt, Refund | Preserve local monetary values; apply explicit FX policies before cross-currency aggregation |
| International text | Customer, Store, Supplier, Product | Preserve source Unicode; derive normalized or localized attributes where required |
| Temporal conformance | ProductPrice, WarehouseAssortment, lifecycle entities | Use business-effective dates and point-in-time relationships |
| Join fan-out | Orders, payments, order items, shipments, returns, refunds | Respect individual grains; aggregate children appropriately before joining |
| Privacy | Customer, LoyaltyMembership, PaymentAttempt | Classify sensitive attributes and restrict unnecessary exposure |
| Simulator information leakage | DemandProfile | Prevent internal latent demand records from entering operational source tables |


## 8. Known modelling boundaries

The following limitations must be considered when using the catalogue for downstream analytical design.

| Boundary | Consequence |
|---|---|
| Store transactions do not enter digital warehouse fulfilment | The WMS ledger must not be interpreted as a complete enterprise-wide retail stock ledger |
| Customer returns originate from outbound shipments | The baseline does not represent a complete in-store returns process |
| No full taxation or discount engine | Recorded order totals cannot independently support comprehensive tax, discount or statutory accounting analysis |
| No financial general ledger | Operational payment and refund measures are not equivalent to audited accounting balances |
| No external FX feed in Phase 1 | Group-currency reporting requires additional reference-data ingestion |
| Availability is generated for the configured snapshot date | Historical availability trends require additional snapshots or defensible reconstruction |
| Source export represents completed generated records | Point-in-time extraction, CDC and change history must be designed separately |
| Operational consequences may occur after the activity window | Extraction cutoffs must prevent future-state information leakage |
| Source identifiers are deterministic within the configured simulation | Cross-simulation identity equivalence must not be assumed |
| Source data is synthetic | Observed distributions demonstrate simulator behaviour, not verified real-world market behaviour |



