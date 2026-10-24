# Mercatural Source Inventory 

## CRM

This is responsible for the customer identiy / profile.

Entities include:

- `customer`
- `customer_contact`
- `customer_address`

The extraction method is a daily snapshot. However, later this will be expanded to account for incremental changes

---

## LOYALTY

Responsible for the customer loyalty membership lifecycle.

Entities include:

- `loyalty_membership`
- `loyalty_tier_event`

This source system will use a daily delta extraction.

---

## PIM

This is responsible for product master data.

Entities include:

- `product`
- `category`
- `brand`

The extraction will be a combination of a snapshot and delta for change products.

---

## PRICING

Responsible for effective-dates prices/promotions

Entities include:

- `product_price`
- `promotion`

Extraction is an effective-dated change feed.

---

## STORE

Responsible for storing the phyical store estate.

Entities include:

- `store`
- `region`

The extraction will use a low frequency shapshot.

---

## OMS

Responsible for the order lifecycle

Entities include:

- `order`
- `order_item`
- `order_status_event`

The OMS source system has multiple channels including:

- STORE
- ECOMMERCE
- MOBILE

The extraction will be an incremental transaction feed

---

## PAYMENTS

Responsible for the payment lifecycle.

Entities Include:

- `payment`
- `payment_event`
- `refund`

The payment events have the following candidates:

- AUTHORIZED
- CAPTURED
- DECLINED
- VOIDED
- REFUNDED

The extraction will be an event feed.

---

## RETURNS

This is responsible for the return lifecycle.

Entities include:

- `return`
- `return_item`

The extraction is an incremental transaction feed.

---

## WMS

Responsible for the inventory state and the stock observations.

Entities include:

- `inventory_position`
- `inventory_event`
- `stock_count`

Candidate inventory events include:

- RECIEPT
- SALE
- RETURN
- ADJUSTMENT
- TRANSFER
- COUNT

The extraction will be a combination of periodic snapshots and event feeds.

---

## PROCUREMENT

Responsible for the supplier / product replenishment lifecycle.

Entities include:

- `supplied`
- `supplier_product`
- `purchase_order`
- `purchase_order_item`

The extraction will be a combination of supplier snapshots and purchase-order delta.

---

## AVAILABILITY

Is responsible for operational avaliability monitoring.

Entities include:

- `avaliability_risk_event`
- `stockout_event`

Extraction will use an event feed.

---

## Summary

| System | Primary extraction |
|---|---|
| CRM | Snapshot / delta |
| LOYALTY | Daily delta |
| PIM | Snapshot + delta |
| PRICING | Effective-dated feed |
| STORE | Snapshot |
| OMS | Incremental transactions |
| PAYMENTS | Event feed |
| RETURNS | Incremental transactions |
| WMS | Snapshot + events |
| PROCUREMENT | Snapshot + incremental |
| AVAILABILITY | Event feed |

---