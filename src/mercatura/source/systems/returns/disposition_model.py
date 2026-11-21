from dataclasses import dataclass
from datetime import date
from typing import Literal

ReturnDispositionType = Literal[
    "RESTOCK",
    "QUARANTINE",
    "WRITE_OFF",
]


RETURN_DISPOSITION_TYPES: tuple[
    ReturnDispositionType,
    ...,
] = (
    "RESTOCK",
    "QUARANTINE",
    "WRITE_OFF",
)


@dataclass(
    frozen=True,
    slots=True,
)
class ReturnDisposition:
    disposition_id: str
    return_id: str
    shipment_id: str
    order_id: str
    order_item_id: str
    market_code: str
    warehouse_assortment_id: str
    warehouse_id: str
    warehouse_code: str
    assortment_id: str
    product_id: str
    sku: str
    disposition_quantity: int
    disposition_type: ReturnDispositionType
    disposition_date: date
