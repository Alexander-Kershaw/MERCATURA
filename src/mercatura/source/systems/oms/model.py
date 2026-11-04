from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

OrderChannel = Literal[
    "STORE",
    "WEB",
    "MOBILE",
]


OrderStatus = Literal[
    "CONFIRMED",
    "CANCELLED",
]


ORDER_CHANNELS: tuple[OrderChannel, ...] = (
    "STORE",
    "WEB",
    "MOBILE",
)


ORDER_STATUSES: tuple[OrderStatus, ...] = (
    "CONFIRMED",
    "CANCELLED",
)


@dataclass(frozen=True, slots=True)
class Order:
    order_id: str
    order_number: str
    customer_id: str
    market_code: str
    currency: str
    channel: OrderChannel
    store_id: str | None
    store_code: str | None
    order_date: date
    order_status: OrderStatus
    cancelled_at: date | None
    order_total: Decimal


@dataclass(frozen=True, slots=True)
class OrderItem:
    order_item_id: str
    order_id: str
    line_number: int
    assortment_id: str
    product_id: str
    sku: str
    price_id: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal
