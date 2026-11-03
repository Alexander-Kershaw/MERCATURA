from dataclasses import dataclass
from datetime import date
from typing import Literal

"""
==================================================================================================

ORDER FULFILMENT MODEL

==================================================================================================

With the purchase order line model established, here I define the order fulfilment model,
which captures the details of the supplier shipments and goods receipts associated 
with a purchase order line.

---------------------------------------------------------------------------------------------------

FulfilmentOutcome is a list of literal values representing the possible outcomes of a supplier
shipment:

- ON_TIME_FULL: The shipment was delivered on time and in full.
- EARLY_FULL: The shipment was delivered early and in full.
- LATE_FULL: The shipment was delivered late but in full.
- SPLIT_FULL: The shipment was delivered in multiple parts, but all parts were delivered in
  full.
- SHORT_SHIPPED: The shipment was delivered, but the quantity received was less than the
  quantity ordered.
- CANCELLED: The shipment was cancelled and not delivered.

---------------------------------------------------------------------------------------------------

The goods receipt model captures the details of the goods received from a supplier shipment,
including the quantity received and the date of receipt.

This ultimately feeds into the warehouse management system.

---------------------------------------------------------------------------------------------------

Note: the SupplierShipment grain is one shipment for one purchase order line, and the 
GoodsReceipt grain is one receipt confirmation for one shipment.

A split purchase order line therefore can produce multiple shipments and multiple receipts.

==================================================================================================
"""

FulfilmentOutcome = Literal[
    "ON_TIME_FULL",
    "EARLY_FULL",
    "LATE_FULL",
    "SPLIT_FULL",
    "SHORT_SHIPPED",
    "CANCELLED",
]


FULFILMENT_OUTCOMES: tuple[FulfilmentOutcome, ...] = (
    "ON_TIME_FULL",
    "EARLY_FULL",
    "LATE_FULL",
    "SPLIT_FULL",
    "SHORT_SHIPPED",
    "CANCELLED",
)


@dataclass(frozen=True, slots=True)
class PurchaseOrderLineFulfilment:
    fulfilment_id: str
    purchase_order_id: str
    purchase_order_line_id: str
    fulfilment_outcome: FulfilmentOutcome


@dataclass(frozen=True, slots=True)
class SupplierShipment:
    shipment_id: str
    shipment_number: str
    purchase_order_id: str
    purchase_order_line_id: str
    sourcing_id: str
    supplier_id: str
    supplier_code: str
    market_code: str
    shipment_sequence: int
    shipped_quantity: int
    shipped_date: date
    delivered_date: date
    fulfilment_outcome: FulfilmentOutcome


@dataclass(frozen=True, slots=True)
class GoodsReceipt:
    goods_receipt_id: str
    receipt_number: str
    shipment_id: str
    purchase_order_id: str
    purchase_order_line_id: str
    market_code: str
    receipt_sequence: int
    received_quantity: int
    received_date: date
