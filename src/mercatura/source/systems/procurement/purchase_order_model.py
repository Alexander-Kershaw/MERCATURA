from dataclasses import dataclass
from datetime import date
from decimal import Decimal

"""
====================================================================================

PURCHASE ORDER DATA MODEL

====================================================================================

This module is composed of two dataclasses:

PurchaseOrder: Represents a purchase order with attributes 
such as purchase_order_id, purchase_order_number, market_code, supplier_id, 
supplier_code, currency, and order_date.

PurchaseOrderLine: Represents a line item within a purchase order,
with attributes such as purchase_order_line_id, purchase_order_id, line_number,
  assortment_id, product_id, sku, sourcing_id, ordered_quantity, unit_cost,
  currency, and expected_delivery_date. It also includes a property method
  line_value that calculates the total value of the line item by multiplying
  the unit cost by the ordered quantity.

------------------------------------------------------------------------------------

The combination of these dataclasses provides a structured data representation
of purchase orders and their associated line items, facilitating the management
and processing of purchase order data within the system.

====================================================================================
"""


@dataclass(frozen=True, slots=True)
class PurchaseOrder:
    purchase_order_id: str
    purchase_order_number: str
    market_code: str
    supplier_id: str
    supplier_code: str
    currency: str
    order_date: date


@dataclass(frozen=True, slots=True)
class PurchaseOrderLine:
    purchase_order_line_id: str
    purchase_order_id: str
    line_number: int
    assortment_id: str
    product_id: str
    sku: str
    sourcing_id: str
    ordered_quantity: int
    unit_cost: Decimal
    currency: str
    expected_delivery_date: date

    @property
    def line_value(self) -> Decimal:
        return self.unit_cost * self.ordered_quantity
