from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from mercatura.source.systems.payments.model import (
    PaymentProcessor,
)

"""
=======================================================================================================

REFUND MODEL

=======================================================================================================

Extending on the payment system here with implementing refund logic. Architecturally, the returns 
system establishes a customer return, which in turn establishes a refund entitlement that is routed 
to the payments system. This issues a refund and references the original payment attempt instance:

    RETURNS system
    CustomerReturn
          │
          │ establishes refund entitlement
          ▼
    PAYMENTS system
    Refund
          │
          └── references original CAPTURED PaymentAttempt


The core economic rule being applied in this logic:

- The refund amount = the original order item unit price multiplied by the returned quantity

Cumulative refunds for an order are to be constrained such that the never exceed the original
payment amount that was captured.

======================================================================================================
"""


RefundStatus = Literal["REFUNDED",]


REFUND_STATUSES: tuple[
    RefundStatus,
    ...,
] = ("REFUNDED",)


@dataclass(
    frozen=True,
    slots=True,
)
class Refund:
    refund_id: str
    refund_reference: str
    return_id: str
    payment_id: str
    payment_reference: str
    order_id: str
    order_item_id: str
    market_code: str
    currency: str
    refunded_quantity: int
    refund_amount: Decimal
    processor: PaymentProcessor
    refund_status: RefundStatus
    refund_date: date
