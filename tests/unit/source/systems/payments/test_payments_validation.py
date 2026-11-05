from dataclasses import replace
from datetime import timedelta, timezone

import pytest

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.oms.model import (
    Order,
)
from mercatura.source.systems.payments.model import (
    PaymentAttempt,
)
from mercatura.source.systems.payments.validation import (
    validate_payment_attempts,
)


def replace_attempt(
    attempts: tuple[PaymentAttempt, ...],
    replacement: PaymentAttempt,
) -> tuple[PaymentAttempt, ...]:
    return tuple(
        replacement if (attempt.payment_id == replacement.payment_id) else attempt
        for attempt in attempts
    )


def validate_small(
    *,
    attempts: tuple[PaymentAttempt, ...],
    orders: tuple[Order, ...],
    context: SimulationContext,
) -> None:
    validate_payment_attempts(
        attempts,
        orders,
        context,
    )


def test_full_dataset_passes_validation(
    payment_attempts: tuple[PaymentAttempt, ...],
    payment_orders: tuple[Order, ...],
    payment_context: SimulationContext,
) -> None:
    validate_payment_attempts(
        payment_attempts,
        payment_orders,
        payment_context,
    )


def test_small_dataset_passes_validation(
    small_payment_attempts: tuple[PaymentAttempt, ...],
    small_payment_orders: tuple[Order, ...],
    payment_context: SimulationContext,
) -> None:
    validate_small(
        attempts=small_payment_attempts,
        orders=small_payment_orders,
        context=payment_context,
    )


def test_rejects_duplicate_payment_id(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    broken = (
        *small_payment_attempts,
        small_payment_attempts[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicate payment_id",
    ):
        validate_small(
            attempts=broken,
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_unknown_order(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    target = small_payment_attempts[0]

    broken = replace(
        target,
        order_id="ord_missing",
    )

    with pytest.raises(
        ValueError,
        match="unknown order",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_amount_mismatch(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    target = small_payment_attempts[0]

    broken = replace(
        target,
        amount=(target.amount + 1),
    )

    with pytest.raises(
        ValueError,
        match="amount does not match",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_market_mismatch(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    target = small_payment_attempts[0]

    broken = replace(
        target,
        market_code="US",
    )

    with pytest.raises(
        ValueError,
        match="market does not match",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_card_missing_network(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    target = next(
        attempt for attempt in small_payment_attempts if (attempt.payment_method == "CARD")
    )

    broken = replace(
        target,
        card_network=None,
    )

    with pytest.raises(
        ValueError,
        match="missing card instrument fields",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_wallet_with_card_fields(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    target = next(
        attempt
        for attempt in small_payment_attempts
        if (attempt.payment_method == "DIGITAL_WALLET")
    )

    broken = replace(
        target,
        card_last_four="1234",
    )

    with pytest.raises(
        ValueError,
        match="conflicting fields",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_bank_payment_with_token(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    target = next(
        attempt for attempt in small_payment_attempts if (attempt.payment_method == "BANK_PAYMENT")
    )

    broken = replace(
        target,
        payment_token="tok_invalid",
    )

    with pytest.raises(
        ValueError,
        match="conflicting instrument fields",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_non_utc_timestamp(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    target = small_payment_attempts[0]

    non_utc = target.initiated_at.astimezone(timezone(timedelta(hours=1)))

    broken = replace(
        target,
        initiated_at=non_utc,
    )

    with pytest.raises(
        ValueError,
        match="stored in UTC",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_declined_without_reason(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    target = next(
        attempt for attempt in small_payment_attempts if (attempt.payment_status == "DECLINED")
    )

    broken = replace(
        target,
        decline_reason=None,
    )

    with pytest.raises(
        ValueError,
        match="decline metadata",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_capture_before_authorization(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    target = next(
        attempt for attempt in small_payment_attempts if (attempt.payment_status == "CAPTURED")
    )

    assert target.authorized_at is not None

    broken = replace(
        target,
        captured_at=(target.authorized_at - timedelta(seconds=1)),
    )

    with pytest.raises(
        ValueError,
        match="capture precedes",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_void_before_authorization(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    target = next(
        attempt for attempt in small_payment_attempts if (attempt.payment_status == "VOIDED")
    )

    assert target.authorized_at is not None

    broken = replace(
        target,
        voided_at=(target.authorized_at - timedelta(seconds=1)),
    )

    with pytest.raises(
        ValueError,
        match="void precedes",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_hard_decline_before_retry(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    attempts_by_order: dict[
        str,
        list[PaymentAttempt],
    ] = {}

    for attempt in small_payment_attempts:
        attempts_by_order.setdefault(
            attempt.order_id,
            [],
        ).append(attempt)

    retrying = next(
        sorted(
            rows,
            key=lambda row: row.attempt_number,
        )
        for rows in attempts_by_order.values()
        if len(rows) > 1
    )

    target = retrying[0]

    broken = replace(
        target,
        decline_type="HARD",
    )

    with pytest.raises(
        ValueError,
        match="requires SOFT decline",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_retry_before_prior_decline(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    attempts_by_order: dict[
        str,
        list[PaymentAttempt],
    ] = {}

    for attempt in small_payment_attempts:
        attempts_by_order.setdefault(
            attempt.order_id,
            [],
        ).append(attempt)

    retrying = next(
        sorted(
            rows,
            key=lambda row: row.attempt_number,
        )
        for rows in attempts_by_order.values()
        if len(rows) > 1
    )

    first = retrying[0]
    second = retrying[1]

    assert first.declined_at is not None

    broken = replace(
        second,
        initiated_at=(first.declined_at),
    )

    with pytest.raises(
        ValueError,
        match="prior decline completes",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )


def test_rejects_instrument_change_during_retry(
    small_payment_attempts,
    small_payment_orders,
    payment_context,
) -> None:
    attempts_by_order: dict[
        str,
        list[PaymentAttempt],
    ] = {}

    for attempt in small_payment_attempts:
        attempts_by_order.setdefault(
            attempt.order_id,
            [],
        ).append(attempt)

    retrying = next(
        sorted(
            rows,
            key=lambda row: row.attempt_number,
        )
        for rows in attempts_by_order.values()
        if (len(rows) > 1 and rows[0].payment_token is not None)
    )

    target = retrying[1]

    broken = replace(
        target,
        payment_token="tok_changed",
    )

    with pytest.raises(
        ValueError,
        match="instrument changes",
    ):
        validate_small(
            attempts=replace_attempt(
                small_payment_attempts,
                broken,
            ),
            orders=small_payment_orders,
            context=payment_context,
        )
