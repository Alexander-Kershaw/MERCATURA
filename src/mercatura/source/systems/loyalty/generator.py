import random
from datetime import date, timedelta

from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.systems.crm.model import (
    Customer,
)
from mercatura.source.systems.loyalty.config import (
    DEFAULT_LOYALTY_CONFIG,
    LoyaltySimulationConfig,
    MarketLoyaltyConfig,
)
from mercatura.source.systems.loyalty.model import (
    LoyaltyMembership,
    LoyaltyTier,
)


def generate_loyalty_memberships(
    context: SimulationContext,
    customers: tuple[Customer, ...],
    *,
    config: LoyaltySimulationConfig = (DEFAULT_LOYALTY_CONFIG),
) -> tuple[LoyaltyMembership, ...]:
    market_configs: dict[str, MarketLoyaltyConfig] = {
        market.market_code: market for market in config.market_configs
    }

    active_markets: set[str] = {market.market_code for market in context.config.markets}

    missing_configs: set[str] = active_markets - set(market_configs)

    if missing_configs:
        missing: str = ", ".join(sorted(missing_configs))

        raise ValueError(f"missing loyalty configuration for markets: {missing}")

    memberships: list[LoyaltyMembership] = []

    for customer in sorted(
        customers,
        key=lambda row: row.customer_number,
    ):
        market_config: MarketLoyaltyConfig | None = market_configs.get(customer.market_code)

        if market_config is None:
            raise ValueError(
                f"customer references market without loyalty configuration: {customer.market_code}"
            )

        membership: LoyaltyMembership | None = _generate_membership(
            context=context,
            customer=customer,
            market_config=(market_config),
            config=config,
        )

        if membership is not None:
            memberships.append(membership)

    return tuple(memberships)


def _generate_membership(
    *,
    context: SimulationContext,
    customer: Customer,
    market_config: MarketLoyaltyConfig,
    config: LoyaltySimulationConfig,
) -> LoyaltyMembership | None:
    rng = random.Random(
        x=context.seed_for(namespace=(f"loyalty:membership:{customer.customer_id}"))
    )

    if rng.random() >= market_config.enrolment_probability:
        return None

    enrolled_at: date | None = _generate_enrolment_date(
        context=context,
        customer=customer,
        rng=rng,
        config=config,
    )

    if enrolled_at is None:
        return None

    tier = _select_tier(
        rng=rng,
        config=config,
    )

    loyalty_number: str = _loyalty_number(customer)

    membership_id: str = context.ids.id_for(
        namespace="loyalty_membership",
        key=customer.customer_id,
        prefix="mem",
    )

    return LoyaltyMembership(
        membership_id=membership_id,
        loyalty_number=loyalty_number,
        customer_id=customer.customer_id,
        market_code=(customer.market_code),
        enrolled_at=enrolled_at,
        tier=tier,
        closed_at=(customer.deactivated_at),
    )


def _generate_enrolment_date(
    *,
    context: SimulationContext,
    customer: Customer,
    rng: random.Random,
    config: LoyaltySimulationConfig,
) -> date | None:
    earliest: date = customer.created_at + timedelta(days=1)

    latest: date = min(
        (customer.created_at + timedelta(days=(config.maximum_enrolment_lag_days))),
        context.config.end_date,
    )

    if customer.deactivated_at is not None:
        latest = min(
            latest,
            (
                customer.deactivated_at
                - timedelta(days=(config.minimum_membership_days_before_closure))
            ),
        )

    if earliest > latest:
        return None

    return _random_date(
        rng=rng,
        start=earliest,
        end=latest,
    )


def _select_tier(
    *,
    rng: random.Random,
    config: LoyaltySimulationConfig,
) -> LoyaltyTier:
    tiers: tuple[LoyaltyTier, ...] = (
        "STANDARD",
        "SILVER",
        "GOLD",
        "PLATINUM",
    )

    weights: tuple[float, float, float, float] = (
        config.standard_tier_probability,
        config.silver_tier_probability,
        config.gold_tier_probability,
        config.platinum_tier_probability,
    )

    return rng.choices(
        population=tiers,
        weights=weights,
        k=1,
    )[0]


def _loyalty_number(
    customer: Customer,
) -> str:
    prefix = "CUS-"

    if not (customer.customer_number.startswith(prefix)):
        raise ValueError("customer_number does not use expected CRM format")

    suffix: str = customer.customer_number[len(prefix) :]

    return f"LOY-{suffix}"


def _random_date(
    *,
    rng: random.Random,
    start: date,
    end: date,
) -> date:
    if start > end:
        raise ValueError("random date start must not be after end")

    span: int = (end - start).days

    return start + timedelta(
        days=rng.randint(
            a=0,
            b=span,
        )
    )
