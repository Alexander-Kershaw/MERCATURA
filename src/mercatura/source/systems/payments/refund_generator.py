from collections import defaultdict
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from mercatura.source.systems.oms.model import (
    OrderItem,
)
from mercatura.source.systems.payments.model import (
    PaymentAttempt,
)
from mercatura.source.systems.payments.refund_model import (
    Refund,
)
from mercatura.source.systems.returns.model import (
    CustomerReturn,
)


def generate_refunds(
    customer_returns: tuple[
        CustomerReturn,
        ...,
    ],
    order_items: tuple[
        OrderItem,
        ...,
    ],
    payment_attempts: tuple[
        PaymentAttempt,
        ...,
    ],
) -> tuple[
    Refund,
    ...,
]:

    order_items_by_id: dict[str, OrderItem] = {
        order_item.order_item_id: order_item for order_item in order_items
    }

    captured_by_order: dict[
        str,
        list[PaymentAttempt],
    ] = defaultdict(list)

    for payment in payment_attempts:
        if payment.payment_status == "CAPTURED":
            captured_by_order[payment.order_id].append(payment)

    refunded_by_payment: dict[
        str,
        Decimal,
    ] = defaultdict(lambda: Decimal("0"))

    refunds: list[Refund] = []

    ordered_returns = sorted(
        customer_returns,
        key=lambda customer_return: (
            customer_return.return_date,
            customer_return.order_id,
            customer_return.order_item_id,
            customer_return.return_id,
        ),
    )

    for customer_return in ordered_returns:
        if customer_return.return_status != "RECEIVED":
            raise ValueError("refund requires a RECEIVED customer return")

        if customer_return.returned_quantity <= 0:
            raise ValueError("refund quantity must be positive")

        order_item = order_items_by_id.get(customer_return.order_item_id)

        if order_item is None:
            raise ValueError("customer return references unknown order item")

        if order_item.order_id != customer_return.order_id:
            raise ValueError("customer return order does not match order item")

        if customer_return.returned_quantity > order_item.quantity:
            raise ValueError("returned quantity exceeds original order item quantity")

        captured_payments = captured_by_order.get(
            customer_return.order_id,
            [],
        )

        if len(captured_payments) != 1:
            raise ValueError("refund requires exactly one CAPTURED payment for order")

        payment = captured_payments[0]

        if payment.captured_at is None:
            raise ValueError("CAPTURED payment has no captured_at timestamp")

        if payment.market_code != customer_return.market_code:
            raise ValueError("payment market does not match customer return")

        if payment.amount <= Decimal("0"):
            raise ValueError("captured payment amount must be positive")

        if order_item.unit_price <= Decimal("0"):
            raise ValueError("order item unit price must be positive")

        refund_amount = order_item.unit_price * Decimal(customer_return.returned_quantity)

        previous_refunds = refunded_by_payment[payment.payment_id]

        new_total = previous_refunds + refund_amount

        if new_total > payment.amount:
            raise ValueError("cumulative refunds exceed captured payment amount")

        refund_id = _stable_id(
            prefix="rfd",
            value=(customer_return.return_id),
        )

        refund = Refund(
            refund_id=refund_id,
            refund_reference=(_refund_reference(refund_id)),
            return_id=(customer_return.return_id),
            payment_id=(payment.payment_id),
            payment_reference=(payment.payment_reference),
            order_id=(customer_return.order_id),
            order_item_id=(customer_return.order_item_id),
            market_code=(customer_return.market_code),
            currency=(payment.currency),
            refunded_quantity=(customer_return.returned_quantity),
            refund_amount=(refund_amount),
            processor=(payment.processor),
            refund_status="REFUNDED",
            refund_date=(customer_return.return_date),
        )

        refunded_by_payment[payment.payment_id] = new_total

        refunds.append(refund)

    return tuple(refunds)


def _stable_id(
    *,
    prefix: str,
    value: str,
) -> str:
    generated = uuid5(
        NAMESPACE_URL,
        (f"mercatura:{prefix}:{value}"),
    )

    return f"{prefix}_{generated.hex[:20]}"


def _refund_reference(
    refund_id: str,
) -> str:
    suffix = refund_id.removeprefix("rfd_").upper()

    return f"RFN-{suffix}"
