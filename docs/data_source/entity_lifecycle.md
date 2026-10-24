# Mercatura Entity and Event Lifecycles

## Customer

Customer will have a lifecycle:

- customer is created
- profile / contact information could be updated
- optional loyalty enrolement 
- customer makes orders
- customer is optionally deactivated 

Key rule:

- customer.created_at <= all dependent customer events

---

## Product

The product lifecycle:

- product is created
- product is priced
- product is stocked
- product is sold
- product is updated
- product is potentially discontinued 

Rules:

- product.created_at <= price.effective_from
- product.created_at <= inventory event
- product.created_at <= order item

---

## Store

The store entity lifecyle:

- store is opened
- the store has physical trading assocated with it
- store is optionally closed

Rule:

- Store-channel orders can only reference a store that is open at the order time.

---

## Order

Orders can follow a successful or cancelled order path.

The successful path:

- CREATED
- CONFIRMED
- FULFILLED
- COMPLETED

Cancellation path:

- CREATED
- CONFIRMED
- CANCELLED

---

## Payment

Payments can have a success and failure path.

Successful path:

- order exists
- the payment is AUTHORIZED
- the payment is CAPTURED
- payment optionally REFUNDED

Failed path:

- order exists
- DECLINED

---

## Return

The return path:

- order item is fulfilled
- the return is requested
- return order item is received
- the return refund is approved
- refund is issued 

Rule:

- Cumalative returned quantity is strictly lower than the fulfilled quantity 

---

## Procurement 

The prodcurement path:

- the supplier is exists
- the purchase order is created
- expected delivery stated
- receipt processed
- inventory increases 

---

## Customer Behaviour

### one time customer

This customer has exactly one completed purchases within the configured observation window.

### returning

Has at least two completed purchases.

### inactive

Has historical completed purchase activity but has not completed a purchases in the trailing inactivity period.

### reactivated

Has historical purchases and a prolonged inactivity gap. But, has a later completed purchase.

### high value

Meets a configured spending / purchase requency critera for definition as a high value customer.

## Cross-system causal chain

```txt
CRM customer
   ↓
OMS order
   ├── PAYMENTS
   ├── WMS stock movement
   ↓
OMS fulfilment
   ↓
optional RETURNS
   ↓
PAYMENTS refund
```

---