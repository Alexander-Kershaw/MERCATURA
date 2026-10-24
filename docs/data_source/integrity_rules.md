# Mercatura Source Integrity Rules

## Rule Families 

I am categorising data integrity rules into distinct families:

- REF    referential
- TEMP   temporal
- LIFE   lifecycle
- VALUE  domain/value
- BEHAV  behavioural
- RECON  reconciliation

The baseline generator is to pass every rule established. The intentional defects are being reported seperately as expected violations to rules.

## Customer Rules

- REF-CUST-001 — CRM customer IDs are unique.
- TEMP-CUST-001 - created_at <= updated_at. 
- TEMP-CUST-002 - created_at < deactivated_at (when deactivated). 

## Loyalty Rules

- REF-LOY-001 — membership references an existing CRM customer.
- TEMP-LOY-001 - customer.created_at <= membership.enrolled_at. 

## Product Rules

- REF-PROD-001 — PIM product IDs are unique.
- LIFE-PROD-001 — product cannot be sold before creation.

## Pricing Rules

- REF-PRICE-001 — every price references a product.
- VALUE-PRICE-001 - price > 0.
- TEMP-PRICE-001 - product.created_at <= effective_from.
- TEMP-PRICE-002 - effective_from < effective_to.
- LIFE-PRICE-001 — standard-price intervals do not overlap for the same product/currency.

## Store Rules

- LIFE-STORE-001 — STORE orders reference a store open at transaction time.

## Orders Rules

- REF-ORDER-001 — order references existing customer.
- REF-ORDER-002 — order item references existing order.
- REF-ORDER-003 — order item references existing product.
- TEMP-ORDER-001 - customer.created_at <= order.created_at.
- TEMP-ORDER-002 - product.created_at <= order_item.created_at.
- TEMP-ORDER-003 - order.created_at <= order_item.created_at.
- LIFE-ORDER-001 — ECOMMERCE does not require a physical store.
- LIFE-ORDER-002 — STORE requires a valid physical store.
- LIFE-ORDER-003 — completed/cancelled are mutually exclusive baseline terminal states.
- VALUE-ORDER-001 - quantity > 0.
- VALUE-ORDER-002 - unit_price >= 0.

## Payments Rules

- REF-PAY-001 — payment references existing order.
- TEMP-PAY-001 - order.created_at <= authorization.
- TEMP-PAY-002 - authorization <= capture.
- TEMP-PAY-003 - capture <= refund.

## Return Rules

- REF-RET-001 — return references eligible fulfilled order item.
- TEMP-RET-001 - fulfilled_at <= return.requested_at.
- VALUE-RET-001 — cumulative returned quantity cannot exceed fulfilled quantity.

## Inventory Rules

- REF-INV-001 — inventory references existing product.
- REF-INV-002 — inventory references valid location.
- TEMP-INV-001 — product exists before inventory event.
- TEMP-INV-002 — location exists before inventory event.
- VALUE-INV-001 — baseline ending stock is non-negative unless an explicit oversell/defect scenario enables otherwise.

## Prodcurement Rules

- REF-PROC-001 — purchase order references existing supplier.
- TEMP-PROC-001 - supplier.created_at <= purchase_order.created_at.
- TEMP-PROC-002 - purchase_order.created_at <= expected_delivery_at.

## Behaviour Rules

- BEHAV-CUST-001 — one_time has exactly one completed order.
- BEHAV-CUST-002 — returning has at least two completed orders.
- BEHAV-CUST-003 — inactive has historical purchases but no purchase in the configured trailing inactivity period.
- BEHAV-CUST-004 — reactivated has earlier purchase + configured inactivity gap + later purchase.
- BEHAV-CUST-005 — high_value satisfies configured spend/frequency policy.

## Reconciliation

- RECON-ORDER-001 — order item values reconcile to order commercial totals according to the defined commercial model.
- RECON-PAY-001 — captures/refunds reconcile to allowed order financial state.

RECON-INV-001:

```txt
opening
+ receipts
+ returns
+ positive adjustments
- sales
- transfers out
- negative adjustments
=
closing
```

---


