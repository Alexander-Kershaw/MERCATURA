from dataclasses import dataclass
from datetime import date
from typing import Literal

ReservationStatus = Literal[
    "RESERVED",
    "RELEASED",
    "CONSUMED",
]


RESERVATION_STATUSES: tuple[
    ReservationStatus,
    ...,
] = (
    "RESERVED",
    "RELEASED",
    "CONSUMED",
)


@dataclass(
    frozen=True,
    slots=True,
)
class InventoryReservation:
    reservation_id: str
    allocation_id: str
    fulfilment_request_id: str
    order_id: str
    order_item_id: str
    market_code: str
    warehouse_assortment_id: str
    warehouse_id: str
    warehouse_code: str
    assortment_id: str
    product_id: str
    sku: str
    reserved_quantity: int
    reservation_status: ReservationStatus
    reserved_date: date
    released_date: date | None
    consumed_date: date | None
