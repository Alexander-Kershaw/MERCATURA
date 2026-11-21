from dataclasses import dataclass
from datetime import date
from typing import Literal

ShipmentStatus = Literal["DISPATCHED",]


SHIPMENT_STATUSES: tuple[
    ShipmentStatus,
    ...,
] = ("DISPATCHED",)


@dataclass(
    frozen=True,
    slots=True,
)
class OutboundShipment:
    shipment_id: str
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
    shipped_quantity: int
    picked_date: date
    dispatched_date: date
    shipment_status: ShipmentStatus
