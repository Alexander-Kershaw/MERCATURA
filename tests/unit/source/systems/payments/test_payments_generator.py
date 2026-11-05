from collections import Counter, defaultdict
from datetime import timedelta
from itertools import pairwise

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.oms.model import (
    Order,
)
from mercatura.source.systems.payments.config import (
    DEFAULT_PAYMENT_CONFIG,
)
from mercatura.source.systems.payments.generator import (
    generate_payment_attempts,
)
from mercatura.source.systems.payments.model import (
    PaymentAttempt,
)


def test_every_order_has_payment_attempt(
    payment_orders: tuple[Order, ...],
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    order_ids = {order.order_id for order in payment_orders}

    paid_order_ids = {attempt.order_id for attempt in payment_attempts}

    assert paid_order_ids == order_ids


def test_payment_attempt_volume_is_reasonable(
    payment_orders: tuple[Order, ...],
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    assert 238_000 < len(payment_attempts) < 244_000

    assert len(payment_attempts) > len(payment_orders)


def test_payment_ids_are_unique(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    ids = [attempt.payment_id for attempt in payment_attempts]

    assert len(ids) == len(set(ids))


def test_payment_references_are_unique(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    references = [attempt.payment_reference for attempt in payment_attempts]

    assert len(references) == len(set(references))


def test_processor_references_are_unique(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    references = [attempt.processor_reference for attempt in payment_attempts]

    assert len(references) == len(set(references))


def test_attempt_count_distribution(
    payment_orders: tuple[Order, ...],
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    counts = Counter(attempt.order_id for attempt in payment_attempts)

    distribution = Counter(counts.values())

    total = len(payment_orders)

    one_attempt = distribution[1] / total

    two_attempts = distribution[2] / total

    three_attempts = distribution[3] / total

    assert 0.90 < one_attempt < 0.94
    assert 0.06 < two_attempts < 0.08
    assert 0.005 < three_attempts < 0.015


def test_confirmed_orders_end_captured(
    payment_orders: tuple[Order, ...],
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    attempts_by_order = _attempts_by_order(payment_attempts)

    for order in payment_orders:
        if order.order_status != "CONFIRMED":
            continue

        final = attempts_by_order[order.order_id][-1]

        assert final.payment_status == "CAPTURED"


def test_cancelled_orders_end_voided(
    payment_orders: tuple[Order, ...],
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    attempts_by_order = _attempts_by_order(payment_attempts)

    for order in payment_orders:
        if order.order_status != "CANCELLED":
            continue

        final = attempts_by_order[order.order_id][-1]

        assert final.payment_status == "VOIDED"


def test_non_final_attempts_are_soft_declines(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    attempts_by_order = _attempts_by_order(payment_attempts)

    for attempts in attempts_by_order.values():
        for attempt in attempts[:-1]:
            assert attempt.payment_status == "DECLINED"

            assert attempt.decline_type == "SOFT"


def test_payment_amount_reconciles_to_order(
    payment_orders: tuple[Order, ...],
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    orders_by_id = {order.order_id: order for order in payment_orders}

    assert all(
        attempt.amount == orders_by_id[attempt.order_id].order_total for attempt in payment_attempts
    )


def test_all_payment_methods_are_present(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    methods = {attempt.payment_method for attempt in payment_attempts}

    assert methods == {
        "CARD",
        "DIGITAL_WALLET",
        "BANK_PAYMENT",
    }


def test_market_instruments_follow_profiles(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    profiles = {profile.market_code: profile for profile in DEFAULT_PAYMENT_CONFIG.market_profiles}

    for attempt in payment_attempts:
        profile = profiles[attempt.market_code]

        if attempt.payment_method == "CARD":
            assert attempt.card_network in profile.card_networks

        elif attempt.payment_method == "DIGITAL_WALLET":
            assert attempt.wallet_provider in profile.wallet_providers

        else:
            assert attempt.bank_payment_rail in profile.bank_payment_rails


def test_store_card_presence_and_entry_mode(
    payment_orders: tuple[Order, ...],
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    orders_by_id = {order.order_id: order for order in payment_orders}

    store_cards = [
        attempt
        for attempt in payment_attempts
        if (attempt.payment_method == "CARD" and orders_by_id[attempt.order_id].channel == "STORE")
    ]

    assert store_cards

    assert all(
        (
            attempt.card_presence == "CARD_PRESENT"
            and attempt.entry_mode
            in {
                "CONTACTLESS",
                "CHIP_PIN",
            }
        )
        for attempt in store_cards
    )


def test_digital_cards_are_card_not_present(
    payment_orders: tuple[Order, ...],
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    orders_by_id = {order.order_id: order for order in payment_orders}

    digital_cards = [
        attempt
        for attempt in payment_attempts
        if (
            attempt.payment_method == "CARD"
            and orders_by_id[attempt.order_id].channel
            in {
                "WEB",
                "MOBILE",
            }
        )
    ]

    assert digital_cards

    assert all(
        (attempt.card_presence == "CARD_NOT_PRESENT" and attempt.entry_mode == "ECOMMERCE")
        for attempt in digital_cards
    )


def test_wallets_use_wallet_token_mode(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    wallets = [
        attempt for attempt in payment_attempts if (attempt.payment_method == "DIGITAL_WALLET")
    ]

    assert wallets

    assert all(
        (
            attempt.wallet_provider is not None
            and attempt.payment_token is not None
            and attempt.entry_mode == "WALLET_TOKEN"
        )
        for attempt in wallets
    )


def test_bank_payments_use_bank_redirect(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    bank_payments = [
        attempt for attempt in payment_attempts if (attempt.payment_method == "BANK_PAYMENT")
    ]

    assert bank_payments

    assert all(
        (
            attempt.bank_payment_rail is not None
            and attempt.payment_token is None
            and attempt.entry_mode == "BANK_REDIRECT"
        )
        for attempt in bank_payments
    )


def test_processor_distribution_is_reasonable(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    final_attempts = _final_attempts(payment_attempts)

    counts = Counter(attempt.processor for attempt in final_attempts)

    total = len(final_attempts)

    assert 0.68 < counts["NORTHSTAR_PAYMENTS"] / total < 0.72

    assert 0.18 < counts["ATLAS_ACQUIRING"] / total < 0.22

    assert 0.08 < counts["HORIZON_PAYMENTS"] / total < 0.12


def test_card_funding_distribution_is_reasonable(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    final_cards = [
        attempt
        for attempt in (_final_attempts(payment_attempts))
        if (attempt.payment_method == "CARD")
    ]

    counts = Counter(attempt.card_funding_type for attempt in final_cards)

    total = len(final_cards)

    assert 0.59 < counts["DEBIT"] / total < 0.65

    assert 0.31 < counts["CREDIT"] / total < 0.37

    assert 0.02 < counts["PREPAID"] / total < 0.06


def test_contactless_share_is_reasonable(
    payment_orders: tuple[Order, ...],
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    orders_by_id = {order.order_id: order for order in payment_orders}

    final_store_cards = [
        attempt
        for attempt in (_final_attempts(payment_attempts))
        if (attempt.payment_method == "CARD" and orders_by_id[attempt.order_id].channel == "STORE")
    ]

    contactless = sum(attempt.entry_mode == "CONTACTLESS" for attempt in final_store_cards)

    share = contactless / len(final_store_cards)

    assert 0.69 < share < 0.75


def test_3ds_challenge_share_is_reasonable(
    payment_orders: tuple[Order, ...],
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    orders_by_id = {order.order_id: order for order in payment_orders}

    captured_remote_cards = [
        attempt
        for attempt in (_final_attempts(payment_attempts))
        if (
            attempt.payment_status == "CAPTURED"
            and attempt.payment_method == "CARD"
            and orders_by_id[attempt.order_id].channel
            in {
                "WEB",
                "MOBILE",
            }
        )
    ]

    challenged = sum(
        attempt.authentication_result == "3DS_CHALLENGE" for attempt in captured_remote_cards
    )

    share = challenged / len(captured_remote_cards)

    assert 0.15 < share < 0.21


def test_timestamps_are_utc(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    for attempt in payment_attempts:
        timestamps = (
            attempt.initiated_at,
            attempt.authorized_at,
            attempt.captured_at,
            attempt.declined_at,
            attempt.voided_at,
        )

        for value in timestamps:
            if value is None:
                continue

            assert value.utcoffset() == timedelta(0)


def test_lifecycle_timestamp_ordering(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    for attempt in payment_attempts:
        if attempt.payment_status == "DECLINED":
            assert attempt.declined_at is not None

            assert attempt.initiated_at < attempt.declined_at

        elif attempt.payment_status == "CAPTURED":
            assert attempt.authorized_at is not None

            assert attempt.captured_at is not None

            assert attempt.initiated_at < attempt.authorized_at < attempt.captured_at

        else:
            assert attempt.authorized_at is not None

            assert attempt.voided_at is not None

            assert attempt.initiated_at < attempt.authorized_at < attempt.voided_at


def test_retry_occurs_after_prior_decline(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    attempts_by_order = _attempts_by_order(payment_attempts)

    for attempts in attempts_by_order.values():
        for previous, current in pairwise(attempts):
            assert previous.declined_at is not None

            assert current.initiated_at > previous.declined_at


def test_payment_tokens_are_reused_across_orders(
    payment_attempts: tuple[PaymentAttempt, ...],
) -> None:
    orders_by_token: dict[
        str,
        set[str],
    ] = defaultdict(set)

    for attempt in payment_attempts:
        token = attempt.payment_token

        if token is None:
            continue

        orders_by_token[token].add(attempt.order_id)

    assert any(len(order_ids) > 1 for order_ids in orders_by_token.values())


def test_generation_is_deterministic(
    payment_context: SimulationContext,
    small_payment_orders: tuple[Order, ...],
) -> None:
    first = generate_payment_attempts(
        payment_context,
        small_payment_orders,
    )

    second = generate_payment_attempts(
        payment_context,
        small_payment_orders,
    )

    assert first == second


def test_order_input_order_independent(
    payment_context: SimulationContext,
    small_payment_orders: tuple[Order, ...],
) -> None:
    first = generate_payment_attempts(
        payment_context,
        small_payment_orders,
    )

    second = generate_payment_attempts(
        payment_context,
        tuple(reversed(small_payment_orders)),
    )

    assert first == second


def _attempts_by_order(
    attempts: tuple[PaymentAttempt, ...],
) -> dict[
    str,
    list[PaymentAttempt],
]:
    grouped: dict[
        str,
        list[PaymentAttempt],
    ] = defaultdict(list)

    for attempt in attempts:
        grouped[attempt.order_id].append(attempt)

    for rows in grouped.values():
        rows.sort(key=lambda row: row.attempt_number)

    return grouped


def _final_attempts(
    attempts: tuple[PaymentAttempt, ...],
) -> list[PaymentAttempt]:
    grouped = _attempts_by_order(attempts)

    return [rows[-1] for rows in grouped.values()]
