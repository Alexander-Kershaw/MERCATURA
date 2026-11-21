from dataclasses import dataclass
from datetime import date
from typing import Literal

ReturnStatus = Literal["RECEIVED",]


ReturnReason = Literal[
    "UNWANTED",
    "WRONG_SIZE_OR_FIT",
    "DAMAGED",
    "FAULTY",
    "NOT_AS_DESCRIBED",
]


RETURN_STATUSES: tuple[
    ReturnStatus,
    ...,
] = ("RECEIVED",)


RETURN_REASONS: tuple[
    ReturnReason,
    ...,
] = (
    "UNWANTED",
    "WRONG_SIZE_OR_FIT",
    "DAMAGED",
    "FAULTY",
    "NOT_AS_DESCRIBED",
)


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerReturn:
    return_id: str
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
    returned_quantity: int
    return_reason: ReturnReason
    return_status: ReturnStatus
    return_date: date
