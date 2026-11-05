from collections import defaultdict
from datetime import timedelta
from itertools import pairwise
from zoneinfo import ZoneInfo

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.oms.model import (
    Order,
)
from mercatura.source.systems.payments.config import (
    DEFAULT_PAYMENT_CONFIG,
    MarketPaymentProfile,
    PaymentSimulationConfig,
)
from mercatura.source.systems.payments.model import (
    CARD_FUNDING_TYPES,
    CARD_NETWORKS,
    PAYMENT_METHODS,
    PAYMENT_PROCESSORS,
    PAYMENT_STATUSES,
    PaymentAttempt,
    PaymentMethod,
    PaymentProcessor,
    PaymentStatus,
)


def validate_payment_attempts(
    attempts: tuple[PaymentAttempt, ...],
    orders: tuple[Order, ...],
    context: SimulationContext,
    *,
    config: PaymentSimulationConfig = (DEFAULT_PAYMENT_CONFIG),
) -> None:
    _validate_uniqueness(attempts)

    _validate_attempts(
        attempts=attempts,
        orders=orders,
        context=context,
        config=config,
    )


def _validate_uniqueness(
    attempts: tuple[PaymentAttempt, ...],
) -> None:
    payment_ids = [attempt.payment_id for attempt in attempts]

    if len(payment_ids) != len(set(payment_ids)):
        raise ValueError("duplicate payment_id detected")

    references = [attempt.payment_reference for attempt in attempts]

    if len(references) != len(set(references)):
        raise ValueError("duplicate payment_reference detected")

    processor_references = [attempt.processor_reference for attempt in attempts]

    if len(processor_references) != len(set(processor_references)):
        raise ValueError("duplicate processor_reference detected")

    order_attempt_pairs = [
        (
            attempt.order_id,
            attempt.attempt_number,
        )
        for attempt in attempts
    ]

    if len(order_attempt_pairs) != len(set(order_attempt_pairs)):
        raise ValueError("duplicate payment attempt number detected")


def _validate_attempts(
    *,
    attempts: tuple[PaymentAttempt, ...],
    orders: tuple[Order, ...],
    context: SimulationContext,
    config: PaymentSimulationConfig,
) -> None:
    orders_by_id = {order.order_id: order for order in orders}

    profiles = {profile.market_code: profile for profile in config.market_profiles}

    attempts_by_order: dict[
        str,
        list[PaymentAttempt],
    ] = defaultdict(list)

    valid_methods = set(PAYMENT_METHODS)

    valid_statuses = set(PAYMENT_STATUSES)

    valid_processors = set(PAYMENT_PROCESSORS)

    for attempt in attempts:
        order = orders_by_id.get(attempt.order_id)

        if order is None:
            raise ValueError("payment attempt references unknown order")

        profile = profiles.get(order.market_code)

        if profile is None:
            raise ValueError("payment attempt references market without profile")

        _validate_basic_fields(
            attempt=attempt,
            order=order,
            valid_methods=valid_methods,
            valid_statuses=valid_statuses,
            valid_processors=valid_processors,
        )

        _validate_timestamp_awareness(attempt)

        _validate_order_timing(
            attempt=attempt,
            order=order,
            context=context,
        )

        _validate_instrument(
            attempt=attempt,
            order=order,
            profile=profile,
        )

        _validate_status_semantics(
            attempt=attempt,
            order=order,
        )

        attempts_by_order[attempt.order_id].append(attempt)

    if set(attempts_by_order) != set(orders_by_id):
        raise ValueError("every order must have payment attempts")

    for order in orders:
        order_attempts = sorted(
            attempts_by_order[order.order_id],
            key=lambda row: row.attempt_number,
        )

        _validate_order_attempt_sequence(
            order=order,
            attempts=order_attempts,
            config=config,
        )


def _validate_basic_fields(
    *,
    attempt: PaymentAttempt,
    order: Order,
    valid_methods: set[PaymentMethod],
    valid_statuses: set[PaymentStatus],
    valid_processors: set[PaymentProcessor],
) -> None:
    if attempt.attempt_number <= 0:
        raise ValueError("payment attempt number must be positive")

    if attempt.payment_method not in valid_methods:
        raise ValueError("payment attempt has invalid method")

    if attempt.payment_status not in valid_statuses:
        raise ValueError("payment attempt has invalid status")

    if attempt.processor not in valid_processors:
        raise ValueError("payment attempt has invalid processor")

    if attempt.market_code != order.market_code:
        raise ValueError("payment market does not match order")

    if attempt.currency != order.currency:
        raise ValueError("payment currency does not match order")

    if attempt.amount != order.order_total:
        raise ValueError("payment amount does not match order total")


def _validate_timestamp_awareness(
    attempt: PaymentAttempt,
) -> None:
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

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payment timestamp must be timezone aware")

        if value.utcoffset() != timedelta(0):
            raise ValueError("payment timestamp must be stored in UTC")


def _validate_order_timing(
    *,
    attempt: PaymentAttempt,
    order: Order,
    context: SimulationContext,
) -> None:
    market = context.market(order.market_code)

    local_zone = ZoneInfo(market.timezone)

    local_initiated_date = attempt.initiated_at.astimezone(local_zone).date()

    if attempt.attempt_number == 1:
        if local_initiated_date != order.order_date:
            raise ValueError("first payment attempt local date does not match order date")

        return

    if local_initiated_date < order.order_date:
        raise ValueError("payment retry local date precedes order date")


def _validate_instrument(
    *,
    attempt: PaymentAttempt,
    order: Order,
    profile: MarketPaymentProfile,
) -> None:
    if attempt.payment_method == "CARD":
        _validate_card(
            attempt=attempt,
            order=order,
            profile=profile,
        )

        return

    if attempt.payment_method == "DIGITAL_WALLET":
        _validate_wallet(
            attempt=attempt,
            profile=profile,
        )

        return

    _validate_bank_payment(
        attempt=attempt,
        profile=profile,
    )


def _validate_card(
    *,
    attempt: PaymentAttempt,
    order: Order,
    profile: MarketPaymentProfile,
) -> None:
    if (
        attempt.card_network is None
        or attempt.card_funding_type is None
        or attempt.card_last_four is None
        or attempt.card_presence is None
        or attempt.payment_token is None
    ):
        raise ValueError("CARD payment is missing card instrument fields")

    if attempt.card_network not in set(profile.card_networks):
        raise ValueError("card network is not valid for payment market")

    if attempt.card_network not in set(CARD_NETWORKS):
        raise ValueError("invalid card network")

    if attempt.card_funding_type not in set(CARD_FUNDING_TYPES):
        raise ValueError("invalid card funding type")

    if len(attempt.card_last_four) != 4 or not (attempt.card_last_four.isdigit()):
        raise ValueError("card_last_four must contain exactly four digits")

    if attempt.wallet_provider is not None or attempt.bank_payment_rail is not None:
        raise ValueError("CARD payment contains fields from another instrument type")

    if order.channel == "STORE":
        if attempt.card_presence != "CARD_PRESENT":
            raise ValueError("STORE card must be card-present")

        if attempt.entry_mode not in {
            "CONTACTLESS",
            "CHIP_PIN",
        }:
            raise ValueError("STORE card has invalid entry mode")

        return

    if attempt.card_presence != "CARD_NOT_PRESENT":
        raise ValueError("digital card must be card-not-present")

    if attempt.entry_mode != "ECOMMERCE":
        raise ValueError("digital card must use ECOMMERCE entry mode")


def _validate_wallet(
    *,
    attempt: PaymentAttempt,
    profile: MarketPaymentProfile,
) -> None:
    if attempt.wallet_provider is None or attempt.payment_token is None:
        raise ValueError("DIGITAL_WALLET payment is missing wallet fields")

    if attempt.wallet_provider not in set(profile.wallet_providers):
        raise ValueError("wallet provider is not valid for payment market")

    if (
        attempt.card_network is not None
        or attempt.card_funding_type is not None
        or attempt.card_last_four is not None
        or attempt.card_presence is not None
        or attempt.bank_payment_rail is not None
    ):
        raise ValueError("DIGITAL_WALLET payment contains conflicting fields")

    if attempt.entry_mode != "WALLET_TOKEN":
        raise ValueError("DIGITAL_WALLET has invalid entry mode")


def _validate_bank_payment(
    *,
    attempt: PaymentAttempt,
    profile: MarketPaymentProfile,
) -> None:
    if attempt.bank_payment_rail is None:
        raise ValueError("BANK_PAYMENT is missing bank payment rail")

    if attempt.bank_payment_rail not in set(profile.bank_payment_rails):
        raise ValueError("bank payment rail is not valid for payment market")

    if (
        attempt.card_network is not None
        or attempt.card_funding_type is not None
        or attempt.card_last_four is not None
        or attempt.card_presence is not None
        or attempt.wallet_provider is not None
        or attempt.payment_token is not None
    ):
        raise ValueError("BANK_PAYMENT contains conflicting instrument fields")

    if attempt.entry_mode != "BANK_REDIRECT":
        raise ValueError("BANK_PAYMENT has invalid entry mode")


def _validate_status_semantics(
    *,
    attempt: PaymentAttempt,
    order: Order,
) -> None:
    if attempt.payment_status == "DECLINED":
        _validate_declined(attempt)

        return

    if attempt.payment_status == "CAPTURED":
        _validate_captured(attempt)

        return

    _validate_voided(
        attempt=attempt,
        order=order,
    )


def _validate_declined(
    attempt: PaymentAttempt,
) -> None:
    if attempt.decline_reason is None or attempt.decline_type is None:
        raise ValueError("DECLINED payment must have decline metadata")

    if (
        attempt.authorized_at is not None
        or attempt.captured_at is not None
        or attempt.voided_at is not None
    ):
        raise ValueError("DECLINED payment has invalid success timestamps")

    if attempt.declined_at is None:
        raise ValueError("DECLINED payment must have declined_at")

    if attempt.declined_at < attempt.initiated_at:
        raise ValueError("DECLINED payment timestamp precedes initiation")


def _validate_captured(
    attempt: PaymentAttempt,
) -> None:
    if (
        attempt.decline_reason is not None
        or attempt.decline_type is not None
        or attempt.declined_at is not None
        or attempt.voided_at is not None
    ):
        raise ValueError("CAPTURED payment contains failure metadata")

    authorized_at = attempt.authorized_at

    captured_at = attempt.captured_at

    if authorized_at is None or captured_at is None:
        raise ValueError("CAPTURED payment is missing success timestamps")

    if authorized_at < attempt.initiated_at:
        raise ValueError("authorization precedes payment initiation")

    if captured_at < authorized_at:
        raise ValueError("capture precedes authorization")

    _validate_success_authentication(attempt)


def _validate_voided(
    *,
    attempt: PaymentAttempt,
    order: Order,
) -> None:
    if (
        attempt.decline_reason is not None
        or attempt.decline_type is not None
        or attempt.declined_at is not None
        or attempt.captured_at is not None
    ):
        raise ValueError("VOIDED payment contains invalid payment metadata")

    authorized_at = attempt.authorized_at

    voided_at = attempt.voided_at

    if authorized_at is None or voided_at is None:
        raise ValueError("VOIDED payment is missing lifecycle timestamps")

    if authorized_at < attempt.initiated_at:
        raise ValueError("authorization precedes payment initiation")

    if voided_at < authorized_at:
        raise ValueError("void precedes authorization")

    if order.cancelled_at is None:
        raise ValueError("VOIDED payment belongs to non-cancelled order")

    _validate_success_authentication(attempt)


def _validate_success_authentication(
    attempt: PaymentAttempt,
) -> None:
    if attempt.payment_method == "CARD":
        if attempt.card_presence == "CARD_NOT_PRESENT":
            if attempt.authentication_result not in {
                "3DS_FRICTIONLESS",
                "3DS_CHALLENGE",
            }:
                raise ValueError("remote card payment has invalid authentication result")

            return

        if attempt.authentication_result != "NOT_APPLICABLE":
            raise ValueError("card-present payment has invalid authentication result")

        return

    if attempt.payment_method == "DIGITAL_WALLET":
        if attempt.authentication_result != "WALLET_AUTHENTICATED":
            raise ValueError("wallet payment has invalid authentication result")

        return

    if attempt.authentication_result != "BANK_AUTHENTICATED":
        raise ValueError("bank payment has invalid authentication result")


def _validate_order_attempt_sequence(
    *,
    order: Order,
    attempts: list[PaymentAttempt],
    config: PaymentSimulationConfig,
) -> None:
    if not attempts:
        raise ValueError("order has no payment attempts")

    maximum_attempts = len(config.failed_attempt_count_probabilities)

    if len(attempts) > maximum_attempts:
        raise ValueError("order has too many payment attempts")

    expected_numbers = list(
        range(
            1,
            len(attempts) + 1,
        )
    )

    actual_numbers = [attempt.attempt_number for attempt in attempts]

    if actual_numbers != expected_numbers:
        raise ValueError("payment attempt numbers are not contiguous")

    for previous, current in pairwise(attempts):
        if current.initiated_at <= previous.initiated_at:
            raise ValueError("payment retry does not occur after prior attempt")

        previous_declined_at = previous.declined_at

        if previous_declined_at is not None and current.initiated_at <= previous_declined_at:
            raise ValueError("payment retry occurs before prior decline completes")

    methods = {attempt.payment_method for attempt in attempts}

    if len(methods) != 1:
        raise ValueError("baseline payment method changes between attempts")

    processors = {attempt.processor for attempt in attempts}

    if len(processors) != 1:
        raise ValueError("baseline processor changes between attempts")

    tokens = {attempt.payment_token for attempt in attempts}

    if len(tokens) != 1:
        raise ValueError("baseline payment instrument changes between attempts")

    for attempt in attempts[:-1]:
        if attempt.payment_status != "DECLINED":
            raise ValueError("non-final payment attempt must be DECLINED")

        if attempt.decline_type != "SOFT":
            raise ValueError("baseline automatic retry requires SOFT decline")

    final_attempt = attempts[-1]

    if order.order_status == "CONFIRMED":
        if final_attempt.payment_status != "CAPTURED":
            raise ValueError("confirmed order must end with CAPTURED payment")

        return

    if final_attempt.payment_status != "VOIDED":
        raise ValueError("cancelled order must end with VOIDED payment")
