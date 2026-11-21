from collections import Counter, defaultdict
from decimal import Decimal

from mercatura.source.systems.oms.model import (
    OrderItem,
)
from mercatura.source.systems.payments.model import (
    PaymentAttempt,
)
from mercatura.source.systems.payments.refund_model import (
    REFUND_STATUSES,
    Refund,
)
from mercatura.source.systems.returns.model import (
    CustomerReturn,
)


def validate_refunds(
    refunds: tuple[
        Refund,
        ...,
    ],
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
) -> None:
    _validate_unique_ids(refunds)

    returns_by_id = {
        customer_return.return_id: customer_return for customer_return in customer_returns
    }

    order_items_by_id = {order_item.order_item_id: order_item for order_item in order_items}

    payments_by_id = {payment.payment_id: payment for payment in payment_attempts}

    refund_counts = Counter(refund.return_id for refund in refunds)

    if set(refund_counts) != set(returns_by_id):
        raise ValueError("refunds do not cover every customer return")

    if any(count != 1 for count in refund_counts.values()):
        raise ValueError("each customer return must produce exactly one refund")

    refunded_by_payment: dict[
        str,
        Decimal,
    ] = defaultdict(lambda: Decimal("0"))

    for refund in refunds:
        customer_return = returns_by_id[refund.return_id]

        order_item = order_items_by_id.get(refund.order_item_id)

        if order_item is None:
            raise ValueError("refund references unknown order item")

        payment = payments_by_id.get(refund.payment_id)

        if payment is None:
            raise ValueError("refund references unknown payment")

        _validate_refund(
            refund,
            customer_return,
            order_item,
            payment,
        )

        refunded_by_payment[payment.payment_id] += refund.refund_amount

    for (
        payment_id,
        refunded_amount,
    ) in refunded_by_payment.items():
        payment = payments_by_id[payment_id]

        if refunded_amount > payment.amount:
            raise ValueError("cumulative refunds exceed captured payment amount")


def _validate_unique_ids(
    refunds: tuple[
        Refund,
        ...,
    ],
) -> None:
    refund_ids = [refund.refund_id for refund in refunds]

    refund_references = [refund.refund_reference for refund in refunds]

    if len(refund_ids) != len(set(refund_ids)):
        raise ValueError("duplicate refund_id detected")

    if len(refund_references) != len(set(refund_references)):
        raise ValueError("duplicate refund_reference detected")


def _validate_refund(
    refund: Refund,
    customer_return: CustomerReturn,
    order_item: OrderItem,
    payment: PaymentAttempt,
) -> None:
    if refund.refund_status not in REFUND_STATUSES:
        raise ValueError("invalid refund status")

    if payment.payment_status != "CAPTURED":
        raise ValueError("refund must reference CAPTURED payment")

    if payment.captured_at is None:
        raise ValueError("CAPTURED payment has no captured_at timestamp")

    if refund.refunded_quantity != customer_return.returned_quantity:
        raise ValueError("refund quantity does not match customer return")

    if refund.refunded_quantity <= 0:
        raise ValueError("refund quantity must be positive")

    if refund.refunded_quantity > order_item.quantity:
        raise ValueError("refund quantity exceeds original order item quantity")

    expected_amount = order_item.unit_price * Decimal(refund.refunded_quantity)

    if refund.refund_amount != expected_amount:
        raise ValueError("refund amount does not match original order item economics")

    if refund.refund_amount <= Decimal("0"):
        raise ValueError("refund amount must be positive")

    if refund.refund_amount > payment.amount:
        raise ValueError("refund amount exceeds captured payment amount")

    if refund.refund_date < customer_return.return_date:
        raise ValueError("refund cannot occur before customer return")

    comparisons = (
        (
            refund.order_id,
            customer_return.order_id,
            "order",
        ),
        (
            refund.order_item_id,
            customer_return.order_item_id,
            "order item",
        ),
        (
            refund.order_id,
            order_item.order_id,
            "order item order",
        ),
        (
            refund.order_id,
            payment.order_id,
            "payment order",
        ),
        (
            refund.market_code,
            customer_return.market_code,
            "market",
        ),
        (
            refund.market_code,
            payment.market_code,
            "payment market",
        ),
        (
            refund.currency,
            payment.currency,
            "currency",
        ),
        (
            refund.payment_reference,
            payment.payment_reference,
            "payment reference",
        ),
        (
            refund.processor,
            payment.processor,
            "processor",
        ),
    )

    for (
        actual,
        expected,
        label,
    ) in comparisons:
        if actual != expected:
            raise ValueError(f"refund {label} mismatch")
