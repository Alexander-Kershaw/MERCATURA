from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

AvailabilityStatus = Literal[
    "IN_STOCK",
    "LOW_STOCK",
    "OUT_OF_STOCK",
    "UNAVAILABLE",
]


AVAILABILITY_STATUSES: tuple[
    AvailabilityStatus,
    ...,
] = (
    "IN_STOCK",
    "LOW_STOCK",
    "OUT_OF_STOCK",
    "UNAVAILABLE",
)


@dataclass(
    frozen=True,
    slots=True,
)
class AvailabilitySnapshot:
    snapshot_id: str
    snapshot_date: date
    market_code: str
    assortment_id: str
    product_id: str
    sku: str
    active_warehouse_count: int
    sellable_on_hand: int
    reserved_quantity: int
    available_to_promise: int
    average_daily_units: Decimal
    days_of_cover: Decimal | None
    availability_status: AvailabilityStatus
