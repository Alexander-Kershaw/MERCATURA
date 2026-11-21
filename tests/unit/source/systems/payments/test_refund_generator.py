from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import cast

import pytest

from mercatura.source.systems.oms.model import (
    OrderItem,
)
from mercatura.source.systems.payments.model import (
    PaymentAttempt,
)
from mercatura.source.systems.payments.refund_generator import (
    generate_refunds,
)
from mercatura.source.systems.payments.refund_validation import (
    validate_refunds,
)
from mercatura.source.systems.returns.model import (
    CustomerReturn,
    ReturnReason,
)

RETURN_DATE = date(
    2024,
    6,
    20,
)


@dataclass(
    frozen=True,
    slots=True,
)
class _OrderItemStub:
    order_item_id: str
    order_id: str
    quantity: int
    unit_price: Decimal


@dataclass(
    frozen=True,
    slots=True,
)
class _PaymentStub:
    payment_id: str
    payment_reference: str
    order_id: str
    market_code: str
    currency: str
    amount: Decimal
    processor: str
    payment_status: str
    captured_at: datetime | None


def _order_item(
    *,
    order_item_id: str = "itm_001",
    order_id: str = "ord_001",
    quantity: int = 4,
    unit_price: Decimal = Decimal("25.00"),
) -> OrderItem:
    return cast(
        OrderItem,
        _OrderItemStub(
            order_item_id=order_item_id,
            order_id=order_id,
            quantity=quantity,
            unit_price=unit_price,
        ),
    )


def _payment(
    *,
    payment_id: str = "pay_001",
    payment_reference: str = "PAY-001-01",
    order_id: str = "ord_001",
    market_code: str = "GB",
    currency: str = "GBP",
    amount: Decimal = Decimal("100.00"),
    payment_status: str = "CAPTURED",
    captured_at: datetime | None = (
        datetime(
            2024,
            6,
            10,
            12,
            0,
            tzinfo=UTC,
        )
    ),
) -> PaymentAttempt:
    return cast(
        PaymentAttempt,
        _PaymentStub(
            payment_id=payment_id,
            payment_reference=(payment_reference),
            order_id=order_id,
            market_code=market_code,
            currency=currency,
            amount=amount,
            processor=("NORTHSTAR_PAYMENTS"),
            payment_status=(payment_status),
            captured_at=captured_at,
        ),
    )


def _return(
    *,
    return_id: str = "ret_001",
    order_id: str = "ord_001",
    order_item_id: str = "itm_001",
    returned_quantity: int = 2,
    market_code: str = "GB",
    return_reason: ReturnReason = ("UNWANTED"),
) -> CustomerReturn:
    return CustomerReturn(
        return_id=return_id,
        shipment_id="shp_001",
        reservation_id="res_001",
        allocation_id="alloc_001",
        fulfilment_request_id="req_001",
        order_id=order_id,
        order_item_id=order_item_id,
        market_code=market_code,
        warehouse_assortment_id=("was_001"),
        warehouse_id="wh_001",
        warehouse_code="GB-WH-001",
        assortment_id="ast_001",
        product_id="prd_001",
        sku="SKU-001",
        returned_quantity=(returned_quantity),
        return_reason=return_reason,
        return_status="RECEIVED",
        return_date=RETURN_DATE,
    )


def test_one_return_creates_one_refund() -> None:
    refunds = generate_refunds(
        (_return(),),
        (_order_item(),),
        (_payment(),),
    )

    assert len(refunds) == 1


def test_no_returns_produce_no_refunds() -> None:
    refunds = generate_refunds(
        (),
        (_order_item(),),
        (_payment(),),
    )

    assert refunds == ()


def test_partial_return_produces_partial_refund() -> None:
    refunds = generate_refunds(
        (
            _return(
                returned_quantity=2,
            ),
        ),
        (
            _order_item(
                quantity=4,
                unit_price=Decimal("25.00"),
            ),
        ),
        (
            _payment(
                amount=Decimal("100.00"),
            ),
        ),
    )

    assert refunds[0].refund_amount == Decimal("50.00")

    assert refunds[0].refunded_quantity == 2


def test_full_return_produces_full_line_refund() -> None:
    refunds = generate_refunds(
        (
            _return(
                returned_quantity=4,
            ),
        ),
        (
            _order_item(
                quantity=4,
                unit_price=Decimal("25.00"),
            ),
        ),
        (
            _payment(
                amount=Decimal("100.00"),
            ),
        ),
    )

    assert refunds[0].refund_amount == Decimal("100.00")


def test_refund_uses_decimal_arithmetic() -> None:
    refunds = generate_refunds(
        (
            _return(
                returned_quantity=3,
            ),
        ),
        (
            _order_item(
                quantity=3,
                unit_price=Decimal("19.99"),
            ),
        ),
        (
            _payment(
                amount=Decimal("59.97"),
            ),
        ),
    )

    assert isinstance(
        refunds[0].refund_amount,
        Decimal,
    )

    assert refunds[0].refund_amount == Decimal("59.97")


def test_refund_references_captured_payment() -> None:
    payment = _payment()

    refund = generate_refunds(
        (_return(),),
        (_order_item(),),
        (payment,),
    )[0]

    assert refund.payment_id == payment.payment_id

    assert refund.payment_reference == payment.payment_reference


def test_refund_preserves_payment_currency() -> None:
    refund = generate_refunds(
        (_return(),),
        (_order_item(),),
        (
            _payment(
                currency="GBP",
            ),
        ),
    )[0]

    assert refund.currency == "GBP"


def test_refund_preserves_payment_processor() -> None:
    payment = _payment()

    refund = generate_refunds(
        (_return(),),
        (_order_item(),),
        (payment,),
    )[0]

    assert refund.processor == payment.processor


def test_refund_date_matches_return_date() -> None:
    refund = generate_refunds(
        (_return(),),
        (_order_item(),),
        (_payment(),),
    )[0]

    assert refund.refund_date == RETURN_DATE


def test_declined_attempt_is_ignored_when_capture_exists() -> None:
    declined = _payment(
        payment_id="pay_declined",
        payment_reference="PAY-001-01",
        payment_status="DECLINED",
        captured_at=None,
    )

    captured = _payment(
        payment_id="pay_captured",
        payment_reference="PAY-001-02",
        payment_status="CAPTURED",
    )

    refund = generate_refunds(
        (_return(),),
        (_order_item(),),
        (
            declined,
            captured,
        ),
    )[0]

    assert refund.payment_id == "pay_captured"


def test_voided_payment_cannot_be_refunded() -> None:
    with pytest.raises(
        ValueError,
        match=("refund requires exactly one CAPTURED payment for order"),
    ):
        generate_refunds(
            (_return(),),
            (_order_item(),),
            (
                _payment(
                    payment_status="VOIDED",
                    captured_at=None,
                ),
            ),
        )


def test_declined_payment_cannot_be_refunded() -> None:
    with pytest.raises(
        ValueError,
        match=("refund requires exactly one CAPTURED payment for order"),
    ):
        generate_refunds(
            (_return(),),
            (_order_item(),),
            (
                _payment(
                    payment_status="DECLINED",
                    captured_at=None,
                ),
            ),
        )


def test_missing_payment_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=("refund requires exactly one CAPTURED payment for order"),
    ):
        generate_refunds(
            (_return(),),
            (_order_item(),),
            (),
        )


def test_multiple_captured_payments_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=("refund requires exactly one CAPTURED payment for order"),
    ):
        generate_refunds(
            (_return(),),
            (_order_item(),),
            (
                _payment(
                    payment_id="pay_001",
                ),
                _payment(
                    payment_id="pay_002",
                    payment_reference=("PAY-001-02"),
                ),
            ),
        )


def test_captured_payment_requires_capture_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match=("CAPTURED payment has no captured_at timestamp"),
    ):
        generate_refunds(
            (_return(),),
            (_order_item(),),
            (
                _payment(
                    payment_status="CAPTURED",
                    captured_at=None,
                ),
            ),
        )


def test_unknown_order_item_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=("customer return references unknown order item"),
    ):
        generate_refunds(
            (
                _return(
                    order_item_id="itm_missing",
                ),
            ),
            (_order_item(),),
            (_payment(),),
        )


def test_return_order_must_match_order_item() -> None:
    with pytest.raises(
        ValueError,
        match=("customer return order does not match order item"),
    ):
        generate_refunds(
            (
                _return(
                    order_id="ord_001",
                ),
            ),
            (
                _order_item(
                    order_id="ord_002",
                ),
            ),
            (_payment(),),
        )


def test_return_quantity_cannot_exceed_order_item() -> None:
    with pytest.raises(
        ValueError,
        match=("returned quantity exceeds original order item quantity"),
    ):
        generate_refunds(
            (
                _return(
                    returned_quantity=5,
                ),
            ),
            (
                _order_item(
                    quantity=4,
                ),
            ),
            (_payment(),),
        )


def test_return_market_must_match_payment() -> None:
    with pytest.raises(
        ValueError,
        match=("payment market does not match customer return"),
    ):
        generate_refunds(
            (
                _return(
                    market_code="GB",
                ),
            ),
            (_order_item(),),
            (
                _payment(
                    market_code="DE",
                ),
            ),
        )


def test_cumulative_refunds_cannot_exceed_capture() -> None:
    returns = (
        _return(
            return_id="ret_001",
            order_item_id="itm_001",
            returned_quantity=2,
        ),
        _return(
            return_id="ret_002",
            order_item_id="itm_002",
            returned_quantity=2,
        ),
    )

    order_items = (
        _order_item(
            order_item_id="itm_001",
            quantity=2,
            unit_price=Decimal("30.00"),
        ),
        _order_item(
            order_item_id="itm_002",
            quantity=2,
            unit_price=Decimal("30.00"),
        ),
    )

    with pytest.raises(
        ValueError,
        match=("cumulative refunds exceed captured payment amount"),
    ):
        generate_refunds(
            returns,
            order_items,
            (
                _payment(
                    amount=Decimal("100.00"),
                ),
            ),
        )


def test_cumulative_refunds_can_equal_capture() -> None:
    returns = (
        _return(
            return_id="ret_001",
            order_item_id="itm_001",
            returned_quantity=2,
        ),
        _return(
            return_id="ret_002",
            order_item_id="itm_002",
            returned_quantity=2,
        ),
    )

    order_items = (
        _order_item(
            order_item_id="itm_001",
            quantity=2,
            unit_price=Decimal("25.00"),
        ),
        _order_item(
            order_item_id="itm_002",
            quantity=2,
            unit_price=Decimal("25.00"),
        ),
    )

    refunds = generate_refunds(
        returns,
        order_items,
        (
            _payment(
                amount=Decimal("100.00"),
            ),
        ),
    )

    assert sum(
        (refund.refund_amount for refund in refunds),
        Decimal("0"),
    ) == Decimal("100.00")


def test_refund_ids_are_unique() -> None:
    returns = (
        _return(
            return_id="ret_001",
            order_item_id="itm_001",
            returned_quantity=1,
        ),
        _return(
            return_id="ret_002",
            order_item_id="itm_002",
            returned_quantity=1,
        ),
    )

    order_items = (
        _order_item(
            order_item_id="itm_001",
        ),
        _order_item(
            order_item_id="itm_002",
        ),
    )

    refunds = generate_refunds(
        returns,
        order_items,
        (_payment(),),
    )

    ids = [refund.refund_id for refund in refunds]

    assert len(ids) == len(set(ids))


def test_generation_is_deterministic() -> None:
    arguments = (
        (_return(),),
        (_order_item(),),
        (_payment(),),
    )

    first = generate_refunds(*arguments)

    second = generate_refunds(*arguments)

    assert first == second


def test_return_input_order_does_not_change_results() -> None:
    returns = (
        _return(
            return_id="ret_001",
            order_item_id="itm_001",
            returned_quantity=1,
        ),
        _return(
            return_id="ret_002",
            order_item_id="itm_002",
            returned_quantity=1,
        ),
    )

    items = (
        _order_item(
            order_item_id="itm_001",
        ),
        _order_item(
            order_item_id="itm_002",
        ),
    )

    payments = (_payment(),)

    first = generate_refunds(
        returns,
        items,
        payments,
    )

    second = generate_refunds(
        tuple(reversed(returns)),
        items,
        payments,
    )

    assert first == second


def test_generated_refunds_pass_validation() -> None:
    customer_returns = (_return(),)

    order_items = (_order_item(),)

    payments = (_payment(),)

    refunds = generate_refunds(
        customer_returns,
        order_items,
        payments,
    )

    validate_refunds(
        refunds,
        customer_returns,
        order_items,
        payments,
    )


def test_validation_rejects_wrong_refund_amount() -> None:
    customer_returns = (_return(),)

    order_items = (_order_item(),)

    payments = (_payment(),)

    refunds = generate_refunds(
        customer_returns,
        order_items,
        payments,
    )

    invalid = (
        replace(
            refunds[0],
            refund_amount=Decimal("999.00"),
        ),
    )

    with pytest.raises(
        ValueError,
        match=("refund amount does not match original order item economics"),
    ):
        validate_refunds(
            invalid,
            customer_returns,
            order_items,
            payments,
        )


def test_validation_rejects_non_captured_payment() -> None:
    customer_returns = (_return(),)

    order_items = (_order_item(),)

    captured = _payment()

    refunds = generate_refunds(
        customer_returns,
        order_items,
        (captured,),
    )

    invalid_payment = _payment(
        payment_status="VOIDED",
        captured_at=None,
    )

    with pytest.raises(
        ValueError,
        match=("refund must reference CAPTURED payment"),
    ):
        validate_refunds(
            refunds,
            customer_returns,
            order_items,
            (invalid_payment,),
        )


def test_validation_rejects_refund_before_return() -> None:
    customer_returns = (_return(),)

    order_items = (_order_item(),)

    payments = (_payment(),)

    refunds = generate_refunds(
        customer_returns,
        order_items,
        payments,
    )

    invalid = (
        replace(
            refunds[0],
            refund_date=date(
                2024,
                6,
                19,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match=("refund cannot occur before customer return"),
    ):
        validate_refunds(
            invalid,
            customer_returns,
            order_items,
            payments,
        )


def test_validation_rejects_wrong_currency() -> None:
    customer_returns = (_return(),)

    order_items = (_order_item(),)

    payments = (
        _payment(
            currency="GBP",
        ),
    )

    refunds = generate_refunds(
        customer_returns,
        order_items,
        payments,
    )

    invalid = (
        replace(
            refunds[0],
            currency="EUR",
        ),
    )

    with pytest.raises(
        ValueError,
        match="refund currency mismatch",
    ):
        validate_refunds(
            invalid,
            customer_returns,
            order_items,
            payments,
        )
