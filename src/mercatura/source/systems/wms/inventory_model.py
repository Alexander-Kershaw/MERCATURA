from dataclasses import dataclass
from datetime import date
from typing import Literal

InventoryMovementType = Literal[
    "RECEIPT",
    "PUTAWAY_OUT",
    "PUTAWAY_IN",
]


InventoryMovementSource = Literal["GOODS_RECEIPT",]


INVENTORY_MOVEMENT_TYPES: tuple[InventoryMovementType, ...] = (
    "RECEIPT",
    "PUTAWAY_OUT",
    "PUTAWAY_IN",
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
