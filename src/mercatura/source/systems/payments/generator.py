import random
from dataclasses import dataclass
from datetime import (
    UTC,
    date,
    datetime,
    time,
    timedelta,
)
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
    AuthenticationResult,
    BankPaymentRail,
    CardFundingType,
    CardNetwork,
    CardPresence,
    DeclineReason,
    DeclineType,
    PaymentAttempt,
    PaymentEntryMode,
    PaymentMethod,
    PaymentProcessor,
    WalletProvider,
)


@dataclass(frozen=True, slots=True)
class _PaymentInstrument:
    payment_method: PaymentMethod

    card_network: CardNetwork | None
    card_funding_type: CardFundingType | None
    card_last_four: str | None
    card_presence: CardPresence | None

    wallet_provider: WalletProvider | None

    bank_payment_rail: BankPaymentRail | None

    payment_token: str | None

    entry_mode: PaymentEntryMode


def generate_payment_attempts(
    context: SimulationContext,
    orders: tuple[Order, ...],
    *,
    config: PaymentSimulationConfig = (DEFAULT_PAYMENT_CONFIG),
) -> tuple[PaymentAttempt, ...]:
    profiles = {profile.market_code: profile for profile in config.market_profiles}

    attempts: list[PaymentAttempt] = []

    for order in sorted(
        orders,
        key=lambda row: row.order_number,
    ):
        profile = profiles.get(order.market_code)

        if profile is None:
            raise ValueError(f"no payment profile configured for market {order.market_code}")

        attempts.extend(
            _generate_order_payment_attempts(
                context=context,
                order=order,
                profile=profile,
                config=config,
            )
        )

    return tuple(attempts)


def _generate_order_payment_attempts(
    *,
    context: SimulationContext,
    order: Order,
    profile: MarketPaymentProfile,
    config: PaymentSimulationConfig,
) -> list[PaymentAttempt]:
    rng = random.Random(context.seed_for(f"payments:order:{order.order_id}"))

    failed_attempt_count = _select_failed_attempt_count(
        rng=rng,
        config=config,
    )

    instrument = _generate_instrument(
        context=context,
        order=order,
        profile=profile,
        rng=rng,
        config=config,
    )

    processor = _select_processor(
        rng=rng,
        config=config,
    )

    base_initiated_at = _generate_base_initiated_at(
        context=context,
        order=order,
        rng=rng,
    )

    attempts: list[PaymentAttempt] = []

    current_initiated_at = base_initiated_at

    for attempt_number in range(
        1,
        failed_attempt_count + 1,
    ):
        decline_reason = _select_decline_reason(
            rng=rng,
            config=config,
        )

        attempts.append(
            _build_declined_attempt(
                context=context,
                order=order,
                attempt_number=(attempt_number),
                instrument=instrument,
                processor=processor,
                decline_reason=(decline_reason),
                initiated_at=(current_initiated_at),
                rng=rng,
            )
        )

        retry_delay = rng.randint(
            config.minimum_retry_delay_seconds,
            config.maximum_retry_delay_seconds,
        )

        current_initiated_at = current_initiated_at + timedelta(seconds=retry_delay)

    final_attempt_number = failed_attempt_count + 1

    if order.order_status == "CONFIRMED":
        attempts.append(
            _build_captured_attempt(
                context=context,
                order=order,
                attempt_number=(final_attempt_number),
                instrument=instrument,
                processor=processor,
                initiated_at=(current_initiated_at),
                rng=rng,
                config=config,
            )
        )

        return attempts

    if order.cancelled_at is None:
        raise ValueError("cancelled OMS order has no cancellation date")

    attempts.append(
        _build_voided_attempt(
            context=context,
            order=order,
            attempt_number=(final_attempt_number),
            instrument=instrument,
            processor=processor,
            initiated_at=(current_initiated_at),
            rng=rng,
            config=config,
        )
    )

    return attempts


def _weighted_choice[T](
    *,
    options: tuple[T, ...],
    weights: tuple[float, ...],
    rng: random.Random,
) -> T:
    return rng.choices(
        population=options,
        weights=weights,
        k=1,
    )[0]


def _select_failed_attempt_count(
    *,
    rng: random.Random,
    config: PaymentSimulationConfig,
) -> int:
    values = tuple(range(len(config.failed_attempt_count_probabilities)))

    return rng.choices(
        population=values,
        weights=(config.failed_attempt_count_probabilities),
        k=1,
    )[0]


def _generate_instrument(
    *,
    context: SimulationContext,
    order: Order,
    profile: MarketPaymentProfile,
    rng: random.Random,
    config: PaymentSimulationConfig,
) -> _PaymentInstrument:
    payment_method = _select_payment_method(
        order=order,
        profile=profile,
        rng=rng,
    )

    if payment_method == "CARD":
        return _generate_card_instrument(
            context=context,
            order=order,
            profile=profile,
            rng=rng,
            config=config,
        )

    if payment_method == "DIGITAL_WALLET":
        return _generate_wallet_instrument(
            context=context,
            order=order,
            profile=profile,
            rng=rng,
        )

    return _generate_bank_instrument(
        order=order,
        profile=profile,
        rng=rng,
    )


def _select_payment_method(
    *,
    order: Order,
    profile: MarketPaymentProfile,
    rng: random.Random,
) -> PaymentMethod:
    methods: tuple[PaymentMethod, ...] = (
        "CARD",
        "DIGITAL_WALLET",
        "BANK_PAYMENT",
    )

    if order.channel == "STORE":
        weights = (
            profile.store_card_probability,
            profile.store_wallet_probability,
            profile.store_bank_payment_probability,
        )
    else:
        weights = (
            profile.digital_card_probability,
            profile.digital_wallet_probability,
            profile.digital_bank_payment_probability,
        )

    return rng.choices(
        population=methods,
        weights=weights,
        k=1,
    )[0]


def _generate_card_instrument(
    *,
    context: SimulationContext,
    order: Order,
    profile: MarketPaymentProfile,
    rng: random.Random,
    config: PaymentSimulationConfig,
) -> _PaymentInstrument:
    network: CardNetwork = _weighted_choice(
        options=profile.card_networks,
        weights=profile.card_network_weights,
        rng=rng,
    )

    funding_type = _select_card_funding_type(
        rng=rng,
        config=config,
    )

    stable_key = f"{order.customer_id}:CARD:{network}:{funding_type}"

    instrument_rng = random.Random(context.seed_for(f"payments:instrument:{stable_key}"))

    last_four = f"{instrument_rng.randint(0, 9999):04d}"

    payment_token = context.ids.id_for(
        "payment_token",
        stable_key,
        prefix="tok",
    )

    if order.channel == "STORE":
        card_presence: CardPresence = "CARD_PRESENT"

        if rng.random() < config.store_contactless_probability:
            entry_mode: PaymentEntryMode = "CONTACTLESS"
        else:
            entry_mode = "CHIP_PIN"
    else:
        card_presence = "CARD_NOT_PRESENT"

        entry_mode = "ECOMMERCE"

    return _PaymentInstrument(
        payment_method="CARD",
        card_network=network,
        card_funding_type=(funding_type),
        card_last_four=last_four,
        card_presence=card_presence,
        wallet_provider=None,
        bank_payment_rail=None,
        payment_token=payment_token,
        entry_mode=entry_mode,
    )


def _select_card_funding_type(
    *,
    rng: random.Random,
    config: PaymentSimulationConfig,
) -> CardFundingType:
    funding_types: tuple[CardFundingType, ...] = (
        "DEBIT",
        "CREDIT",
        "PREPAID",
    )

    return rng.choices(
        population=funding_types,
        weights=(
            config.debit_probability,
            config.credit_probability,
            config.prepaid_probability,
        ),
        k=1,
    )[0]


def _generate_wallet_instrument(
    *,
    context: SimulationContext,
    order: Order,
    profile: MarketPaymentProfile,
    rng: random.Random,
) -> _PaymentInstrument:
    provider: WalletProvider = _weighted_choice(
        options=profile.wallet_providers,
        weights=profile.wallet_provider_weights,
        rng=rng,
    )

    stable_key = f"{order.customer_id}:WALLET:{provider}"

    payment_token = context.ids.id_for(
        "payment_token",
        stable_key,
        prefix="tok",
    )

    return _PaymentInstrument(
        payment_method=("DIGITAL_WALLET"),
        card_network=None,
        card_funding_type=None,
        card_last_four=None,
        card_presence=None,
        wallet_provider=provider,
        bank_payment_rail=None,
        payment_token=payment_token,
        entry_mode="WALLET_TOKEN",
    )


def _generate_bank_instrument(
    *,
    order: Order,
    profile: MarketPaymentProfile,
    rng: random.Random,
) -> _PaymentInstrument:
    del order

    rail: BankPaymentRail = _weighted_choice(
        options=profile.bank_payment_rails,
        weights=profile.bank_payment_rail_weights,
        rng=rng,
    )

    return _PaymentInstrument(
        payment_method="BANK_PAYMENT",
        card_network=None,
        card_funding_type=None,
        card_last_four=None,
        card_presence=None,
        wallet_provider=None,
        bank_payment_rail=rail,
        payment_token=None,
        entry_mode="BANK_REDIRECT",
    )


def _select_processor(
    *,
    rng: random.Random,
    config: PaymentSimulationConfig,
) -> PaymentProcessor:
    processors: tuple[PaymentProcessor, ...] = (
        "NORTHSTAR_PAYMENTS",
        "ATLAS_ACQUIRING",
        "HORIZON_PAYMENTS",
    )

    return rng.choices(
        population=processors,
        weights=(
            config.northstar_processor_probability,
            config.atlas_processor_probability,
            config.horizon_processor_probability,
        ),
        k=1,
    )[0]


def _generate_base_initiated_at(
    *,
    context: SimulationContext,
    order: Order,
    rng: random.Random,
) -> datetime:
    market = context.market(order.market_code)

    local_zone = ZoneInfo(market.timezone)

    if order.channel == "STORE":
        hour = rng.randint(
            9,
            20,
        )
    else:
        hour = rng.randint(
            0,
            23,
        )

    minute = rng.randint(
        0,
        59,
    )

    second = rng.randint(
        0,
        59,
    )

    local_datetime = datetime.combine(
        order.order_date,
        time(
            hour=hour,
            minute=minute,
            second=second,
        ),
        tzinfo=local_zone,
    )

    return local_datetime.astimezone(UTC)


def _select_authentication_result(
    *,
    instrument: _PaymentInstrument,
    order: Order,
    rng: random.Random,
    config: PaymentSimulationConfig,
) -> AuthenticationResult:
    if instrument.payment_method == "CARD":
        if order.channel == "STORE":
            return "NOT_APPLICABLE"

        if rng.random() < config.three_ds_challenge_probability:
            return "3DS_CHALLENGE"

        return "3DS_FRICTIONLESS"

    if instrument.payment_method == "DIGITAL_WALLET":
        return "WALLET_AUTHENTICATED"

    return "BANK_AUTHENTICATED"


def _select_decline_reason(
    *,
    rng: random.Random,
    config: PaymentSimulationConfig,
) -> DeclineReason:
    reasons: tuple[DeclineReason, ...] = (
        "INSUFFICIENT_FUNDS",
        "DO_NOT_HONOUR",
        "LIMIT_EXCEEDED",
        "PROCESSOR_ERROR",
    )

    return rng.choices(
        population=reasons,
        weights=(
            config.insufficient_funds_probability,
            config.do_not_honour_probability,
            config.limit_exceeded_probability,
            config.processor_error_probability,
        ),
        k=1,
    )[0]


def _decline_type(
    reason: DeclineReason,
) -> DeclineType:
    if reason in {
        "EXPIRED_INSTRUMENT",
        "INVALID_DETAILS",
        "SUSPECTED_FRAUD",
    }:
        return "HARD"

    return "SOFT"


def _build_declined_attempt(
    *,
    context: SimulationContext,
    order: Order,
    attempt_number: int,
    instrument: _PaymentInstrument,
    processor: PaymentProcessor,
    decline_reason: DeclineReason,
    initiated_at: datetime,
    rng: random.Random,
) -> PaymentAttempt:
    declined_at = initiated_at + timedelta(
        seconds=rng.randint(
            1,
            8,
        )
    )

    return PaymentAttempt(
        payment_id=_payment_id(
            context=context,
            order=order,
            attempt_number=attempt_number,
        ),
        payment_reference=(
            _payment_reference(
                order=order,
                attempt_number=attempt_number,
            )
        ),
        processor_reference=(
            _processor_reference(
                context=context,
                order=order,
                attempt_number=attempt_number,
                processor=processor,
            )
        ),
        order_id=order.order_id,
        attempt_number=attempt_number,
        market_code=order.market_code,
        currency=order.currency,
        amount=order.order_total,
        payment_method=(instrument.payment_method),
        processor=processor,
        card_network=(instrument.card_network),
        card_funding_type=(instrument.card_funding_type),
        card_last_four=(instrument.card_last_four),
        card_presence=(instrument.card_presence),
        wallet_provider=(instrument.wallet_provider),
        bank_payment_rail=(instrument.bank_payment_rail),
        payment_token=(instrument.payment_token),
        entry_mode=(instrument.entry_mode),
        authentication_result=("NOT_APPLICABLE"),
        payment_status="DECLINED",
        decline_reason=decline_reason,
        decline_type=(_decline_type(decline_reason)),
        initiated_at=initiated_at,
        authorized_at=None,
        captured_at=None,
        declined_at=declined_at,
        voided_at=None,
    )


def _build_captured_attempt(
    *,
    context: SimulationContext,
    order: Order,
    attempt_number: int,
    instrument: _PaymentInstrument,
    processor: PaymentProcessor,
    initiated_at: datetime,
    rng: random.Random,
    config: PaymentSimulationConfig,
) -> PaymentAttempt:
    authorized_at = initiated_at + timedelta(
        seconds=rng.randint(
            1,
            5,
        )
    )

    if order.channel == "STORE":
        capture_delay = rng.randint(
            config.minimum_store_capture_delay_seconds,
            config.maximum_store_capture_delay_seconds,
        )
    else:
        capture_delay = rng.randint(
            config.minimum_digital_capture_delay_seconds,
            config.maximum_digital_capture_delay_seconds,
        )

    captured_at = authorized_at + timedelta(seconds=capture_delay)

    authentication_result = _select_authentication_result(
        instrument=instrument,
        order=order,
        rng=rng,
        config=config,
    )

    return PaymentAttempt(
        payment_id=_payment_id(
            context=context,
            order=order,
            attempt_number=attempt_number,
        ),
        payment_reference=(
            _payment_reference(
                order=order,
                attempt_number=attempt_number,
            )
        ),
        processor_reference=(
            _processor_reference(
                context=context,
                order=order,
                attempt_number=attempt_number,
                processor=processor,
            )
        ),
        order_id=order.order_id,
        attempt_number=attempt_number,
        market_code=order.market_code,
        currency=order.currency,
        amount=order.order_total,
        payment_method=(instrument.payment_method),
        processor=processor,
        card_network=(instrument.card_network),
        card_funding_type=(instrument.card_funding_type),
        card_last_four=(instrument.card_last_four),
        card_presence=(instrument.card_presence),
        wallet_provider=(instrument.wallet_provider),
        bank_payment_rail=(instrument.bank_payment_rail),
        payment_token=(instrument.payment_token),
        entry_mode=(instrument.entry_mode),
        authentication_result=(authentication_result),
        payment_status="CAPTURED",
        decline_reason=None,
        decline_type=None,
        initiated_at=initiated_at,
        authorized_at=authorized_at,
        captured_at=captured_at,
        declined_at=None,
        voided_at=None,
    )


def _build_voided_attempt(
    *,
    context: SimulationContext,
    order: Order,
    attempt_number: int,
    instrument: _PaymentInstrument,
    processor: PaymentProcessor,
    initiated_at: datetime,
    rng: random.Random,
    config: PaymentSimulationConfig,
) -> PaymentAttempt:
    cancelled_at = order.cancelled_at

    if cancelled_at is None:
        raise ValueError("cannot create VOIDED payment without order cancellation")

    authorized_at = initiated_at + timedelta(
        seconds=rng.randint(
            1,
            5,
        )
    )

    voided_at = _generate_voided_at(
        context=context,
        order=order,
        cancellation_date=(cancelled_at),
        authorized_at=(authorized_at),
        rng=rng,
    )

    authentication_result = _select_authentication_result(
        instrument=instrument,
        order=order,
        rng=rng,
        config=config,
    )

    return PaymentAttempt(
        payment_id=_payment_id(
            context=context,
            order=order,
            attempt_number=attempt_number,
        ),
        payment_reference=(
            _payment_reference(
                order=order,
                attempt_number=attempt_number,
            )
        ),
        processor_reference=(
            _processor_reference(
                context=context,
                order=order,
                attempt_number=attempt_number,
                processor=processor,
            )
        ),
        order_id=order.order_id,
        attempt_number=attempt_number,
        market_code=order.market_code,
        currency=order.currency,
        amount=order.order_total,
        payment_method=(instrument.payment_method),
        processor=processor,
        card_network=(instrument.card_network),
        card_funding_type=(instrument.card_funding_type),
        card_last_four=(instrument.card_last_four),
        card_presence=(instrument.card_presence),
        wallet_provider=(instrument.wallet_provider),
        bank_payment_rail=(instrument.bank_payment_rail),
        payment_token=(instrument.payment_token),
        entry_mode=(instrument.entry_mode),
        authentication_result=(authentication_result),
        payment_status="VOIDED",
        decline_reason=None,
        decline_type=None,
        initiated_at=initiated_at,
        authorized_at=authorized_at,
        captured_at=None,
        declined_at=None,
        voided_at=voided_at,
    )


def _generate_voided_at(
    *,
    context: SimulationContext,
    order: Order,
    cancellation_date: date,
    authorized_at: datetime,
    rng: random.Random,
) -> datetime:
    if cancellation_date == order.order_date:
        return authorized_at + timedelta(
            minutes=rng.randint(
                10,
                180,
            )
        )

    market = context.market(order.market_code)

    local_zone = ZoneInfo(market.timezone)

    local_voided_at = datetime.combine(
        cancellation_date,
        time(
            hour=rng.randint(
                8,
                22,
            ),
            minute=rng.randint(
                0,
                59,
            ),
            second=rng.randint(
                0,
                59,
            ),
        ),
        tzinfo=local_zone,
    )

    voided_at = local_voided_at.astimezone(UTC)

    if voided_at <= authorized_at:
        return authorized_at + timedelta(minutes=10)

    return voided_at


def _payment_id(
    *,
    context: SimulationContext,
    order: Order,
    attempt_number: int,
) -> str:
    stable_key = f"{order.order_id}:{attempt_number}"

    return context.ids.id_for(
        "payment_attempt",
        stable_key,
        prefix="pay",
    )


def _payment_reference(
    *,
    order: Order,
    attempt_number: int,
) -> str:
    prefix = "ORD-"

    if not (order.order_number.startswith(prefix)):
        raise ValueError("order_number does not use expected OMS format")

    suffix = order.order_number[len(prefix) :]

    return f"PAY-{suffix}-{attempt_number:02d}"


def _processor_reference(
    *,
    context: SimulationContext,
    order: Order,
    attempt_number: int,
    processor: PaymentProcessor,
) -> str:
    stable_key = f"{processor}:{order.order_id}:{attempt_number}"

    return context.ids.id_for(
        "processor_reference",
        stable_key,
        prefix="psp",
    )
