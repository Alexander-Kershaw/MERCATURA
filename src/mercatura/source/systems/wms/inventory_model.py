from dataclasses import dataclass
from datetime import date
from typing import Literal

"""
===========================================================================================

INVENTORY MODEL

===========================================================================================

REFACTOR NOTES: 

- Opening inventory balances are used here to solve a temporal issue. Considering the
retail simulation begins on 2024-01-01, but warehouses already exist before 2024 (as 
expected as this is a modernisation project), and product assortments were already 
stocked before 2024. Therefore the starting inventory should not be zero, there must be
an opening balance to represent the existing state before the hypothetical modernisation
taking place on 2024-01-01.

With the absence of an opening inventory, the 2024 January demand would be forced to
consume stock that only appears after the simulated procurement receipts are generated 
which would result in stockouts due to a poor simulator temporal boundary rather than 
emulating realistic retailer behaviour. 

The corrected accounting model is:

- Opening balance exists
- Goods receipts are generated
- This results in future outbound movement of stock
- Adjustments and returns are applied
- The result of these factors describes the inventory on hand

Note that nothing about the existing receipt and putaway implementation has changed, it
has just been expanded to account for the opening balance consideration.

Importantly, the semantics of OPENING_BALANCE does not mean a procurement receipt,
it means that this stock existed before the simulation temporal window began.

-------------------------------------------------------------------------------------------

REFACTOR NOTES:

This additional refactor taks into account the following progress, so far I have:

- Allocation: deciding which stock can satisfy demand
- Reservation: creates an operational hold of stock reserved for dispatch
- Pick/Dispatch: Physically removes stock from the WMS

Now the movement of stock is like:

            BULK_STORAGE
            │
            │ PICK_OUT  -Q
            ▼
            PICK_FACE
            │ PICK_IN   +Q
            │
            │ DISPATCH  -Q
            ▼
            Customer shipment

Net physical inventory movement = -Q

-------------------------------------------------------------------------------------------

REFACTOR NOTES:

Added in customer return logic, so a return receipt InventoryMovementType and a 
customer return InventoryMovementSource has been added.

The physical inventory is now: Opening inventory + goods receipts - dispatch + customer
returns received,

A customer return gets routed to the RETURNS zone and is not made sellable instantagouesly
this is because returns can mean defective product so immediately exposing a defective
product and making it sellable would not be realistic.

-------------------------------------------------------------------------------------------

REFACTOR NOTES:

Enhanced the return logic with return disposition. Example flow:

        RETURNS
        ├── RESTOCK
        │     RETURN_TRANSFER_OUT -Q
        │     RESTOCK_IN          +Q → BULK_STORAGE
        │
        ├── QUARANTINE
        │     RETURN_TRANSFER_OUT -Q
        │     QUARANTINE_IN       +Q → QUARANTINE
        │
        └── WRITE_OFF
            WRITE_OFF           -Q

The restock / quarantine are location transfers, meaning the total physical inventory 
does not change, while write off reduces the physical inventory.

===========================================================================================
"""

InventoryMovementType = Literal[
    "OPENING_BALANCE",
    "RECEIPT",
    "PUTAWAY_OUT",
    "PUTAWAY_IN",
    "PICK_OUT",
    "PICK_IN",
    "DISPATCH",
    "RETURN_RECEIPT",
    "RETURN_TRANSFER_OUT",
    "RESTOCK_IN",
    "QUARANTINE_IN",
    "WRITE_OFF",
]

INVENTORY_MOVEMENT_TYPES: tuple[InventoryMovementType, ...] = (
    "OPENING_BALANCE",
    "RECEIPT",
    "PUTAWAY_OUT",
    "PUTAWAY_IN",
    "PICK_OUT",
    "PICK_IN",
    "DISPATCH",
    "RETURN_RECEIPT",
    "RETURN_TRANSFER_OUT",
    "RESTOCK_IN",
    "QUARANTINE_IN",
    "WRITE_OFF",
)

InventoryMovementSource = Literal[
    "OPENING_BALANCE",
    "GOODS_RECEIPT",
    "FULFILMENT_SHIPMENT",
    "CUSTOMER_RETURN",
    "RETURN_DISPOSITION",
]


INVENTORY_MOVEMENT_SOURCES: tuple[InventoryMovementSource, ...] = (
    "OPENING_BALANCE",
    "GOODS_RECEIPT",
    "FULFILMENT_SHIPMENT",
    "CUSTOMER_RETURN",
    "RETURN_DISPOSITION",
)


@dataclass(frozen=True, slots=True)
class InventoryMovement:
    movement_id: str
    movement_group_id: str
    movement_sequence: int
    movement_type: InventoryMovementType
    source_reference_type: InventoryMovementSource
    source_reference_id: str
    market_code: str
    warehouse_id: str
    warehouse_code: str
    inventory_location_id: str
    location_code: str
    assortment_id: str
    product_id: str
    sku: str
    quantity_delta: int
    event_date: date
