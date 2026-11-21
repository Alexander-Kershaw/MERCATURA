from dataclasses import dataclass
from datetime import date
from typing import Literal

"""
========================================================================================================

FULFILMENT MODEL

========================================================================================================

This script details the fulfilment model. These datablass definitions form the backbone of the
overall data fields used to accomplish the following flow of data:

            confirmed WEB/MOBILE OrderItem
                          │
                  FulfilmentRequest
                          │
              examine sellable inventory
              available on order date
                          │
            rank eligible warehouses by
                  stocking_priority
                          │
                  allocate stock
                    /          \
                  /             \
            fully allocated   remainder
                │                │
            ALLOCATED       PARTIAL/BACKORDERED


Note that the implementation will maintain a working inventory balance WHILE processing orders.
This would avoid two different orders being allocated against the same physical unit before I
implement the next part of the simulator that generates actual outbound ledger events.

--------------------------------------------------------------------------------------------------------

The inventory input is OPENING_BALANCE + PUTAWAY_IN, so basically any stock movements in sellable
locations effective by the allocation date.

Also, splitting between FulfilmentRequest and FulfilmentAllocation is intentional. Consider the
following case:

- A customer requests 4 units, warehouse A can supply 3, warehouse B can supply 1

This gives:

    FulfilmentRequest
    requested=4
    allocated=4
    unallocated=0
    status=ALLOCATED

    Allocation 1
    WH-A = 3

    Allocation 2
    WH-B = 1

OR, if only two exist:

    requested=4
    allocated=2
    unallocated=2
    status=PARTIALLY_ALLOCATED

This allows the explicity business state to be preserved instead of rellying on the absence of 
allocation rows to mean a multitude of different things.

========================================================================================================
"""


FulfilmentAllocationStatus = Literal[
    "ALLOCATED",
    "PARTIALLY_ALLOCATED",
    "BACKORDERED",
]


FULFILMENT_ALLOCATION_STATUSES: tuple[FulfilmentAllocationStatus, ...] = (
    "ALLOCATED",
    "PARTIALLY_ALLOCATED",
    "BACKORDERED",
)


@dataclass(frozen=True, slots=True)
class FulfilmentRequest:
    fulfilment_request_id: str
    order_id: str
    order_number: str
    order_item_id: str
    line_number: int
    market_code: str
    channel: str
    assortment_id: str
    product_id: str
    sku: str
    requested_quantity: int
    allocated_quantity: int
    unallocated_quantity: int
    allocation_status: FulfilmentAllocationStatus
    allocation_date: date


@dataclass(frozen=True, slots=True)
class FulfilmentAllocation:
    allocation_id: str
    fulfilment_request_id: str
    order_id: str
    order_item_id: str
    allocation_sequence: int
    market_code: str
    warehouse_assortment_id: str
    warehouse_id: str
    warehouse_code: str
    assortment_id: str
    product_id: str
    sku: str
    allocated_quantity: int
    allocation_date: date
