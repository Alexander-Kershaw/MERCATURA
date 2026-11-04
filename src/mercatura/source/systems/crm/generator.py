import random
from collections import defaultdict
from datetime import date, timedelta
from typing import Protocol, cast

from faker import Faker

from mercatura.source.reference.customer_geography import (
    CUSTOMER_GEOGRAPHIES,
    CustomerGeography,
)
from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.simulation.market import MarketConfig
from mercatura.source.systems.crm.config import (
    DEFAULT_CUSTOMER_CONFIG,
    CustomerPopulation,
    CustomerSimulationConfig,
)
from mercatura.source.systems.crm.model import (
    Customer,
)


class _CustomerFaker(Protocol):
    def seed_instance(
        self,
        seed: int,
    ) -> None: ...

    def first_name(
        self,
    ) -> str: ...

    def last_name(
        self,
    ) -> str: ...

    def postcode(
        self,
    ) -> str: ...

    def phone_number(
        self,
    ) -> str: ...


def generate_customers(
    context: SimulationContext,
    *,
    config: CustomerSimulationConfig = (DEFAULT_CUSTOMER_CONFIG),
) -> tuple[Customer, ...]:
    active_markets: dict[str, MarketConfig] = {
        market.market_code: market for market in context.config.markets
    }

    populations: dict[str, CustomerPopulation] = {
        population.market_code: population for population in config.populations
    }

    geography_by_market: dict[str, tuple[CustomerGeography, ...]] = _group_geography_by_market()

    customers: list[Customer] = []

    for market_code in sorted(active_markets):
        population: CustomerPopulation | None = populations.get(market_code)

        if population is None:
            raise ValueError(f"no CRM population configured for market {market_code}")

        geography: tuple[CustomerGeography, ...] | None = geography_by_market.get(market_code)

        if not geography:
            raise ValueError(f"no customer geography configured for market {market_code}")

        market: MarketConfig = active_markets[market_code]

        fake: _CustomerFaker = cast(
            _CustomerFaker,
            Faker(market.locale),
        )

        fake.seed_instance(seed=context.seed_for(namespace=f"crm:faker:{market_code}"))

        customers.extend(
            _generate_market_customers(
                context=context,
                market_code=market_code,
                population=population,
                geography=geography,
                fake=fake,
                config=config,
            )
        )

    return tuple(customers)


def _generate_market_customers(
    *,
    context: SimulationContext,
    market_code: str,
    population: CustomerPopulation,
    geography: tuple[CustomerGeography, ...],
    fake: _CustomerFaker,
    config: CustomerSimulationConfig,
) -> list[Customer]:
    customers: list[Customer] = []

    for ordinal in range(
        1,
        population.customer_count + 1,
    ):
        customer_number: str = f"CUS-{market_code}-{ordinal:06d}"

        rng = random.Random(
            x=context.seed_for(namespace=(f"crm:customer:{market_code}:{ordinal:06d}"))
        )

        location: CustomerGeography = geography[rng.randrange(len(geography))]

        created_at: date = _generate_created_at(
            context=context,
            rng=rng,
            config=config,
        )

        deactivated_at: date | None = _generate_deactivated_at(
            context=context,
            created_at=created_at,
            rng=rng,
            config=config,
        )

        first_name: str = (fake.first_name()).strip()

        last_name: str = (fake.last_name()).strip()

        email: str | None = _generate_email(
            market_code=market_code,
            ordinal=ordinal,
            rng=rng,
            config=config,
        )

        phone: str | None = _generate_phone(
            fake=fake,
            rng=rng,
            config=config,
        )

        if email is None and phone is None:
            email = _customer_email(
                market_code=market_code,
                ordinal=ordinal,
            )

        postal_code: str = str(object=fake.postcode()).strip()

        if not postal_code:
            postal_code = f"SYN-{market_code}-{ordinal:06d}"

        customer_id: str = context.ids.id_for(
            namespace="customer",
            key=customer_number,
            prefix="cus",
        )

        customers.append(
            Customer(
                customer_id=customer_id,
                customer_number=(customer_number),
                market_code=market_code,
                country_code=market_code,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                city=location.city,
                region=location.region,
                postal_code=postal_code,
                created_at=created_at,
                deactivated_at=(deactivated_at),
            )
        )

    return customers


def _generate_created_at(
    *,
    context: SimulationContext,
    rng: random.Random,
    config: CustomerSimulationConfig,
) -> date:
    if rng.random() < config.created_during_simulation_share:
        return _random_date(
            rng=rng,
            start=context.config.start_date,
            end=context.config.end_date,
        )

    historical_start: date = context.config.start_date - timedelta(days=365 * config.history_years)

    historical_end: date = context.config.start_date - timedelta(days=1)

    return _random_date(
        rng=rng,
        start=historical_start,
        end=historical_end,
    )


def _generate_deactivated_at(
    *,
    context: SimulationContext,
    created_at: date,
    rng: random.Random,
    config: CustomerSimulationConfig,
) -> date | None:
    if rng.random() >= config.deactivation_probability:
        return None

    earliest: date = max(
        created_at + timedelta(days=config.minimum_active_days),
        context.config.start_date,
    )

    if earliest > context.config.end_date:
        return None

    return _random_date(
        rng=rng,
        start=earliest,
        end=context.config.end_date,
    )


def _generate_email(
    *,
    market_code: str,
    ordinal: int,
    rng: random.Random,
    config: CustomerSimulationConfig,
) -> str | None:
    if rng.random() < config.missing_email_probability:
        return None

    return _customer_email(
        market_code=market_code,
        ordinal=ordinal,
    )


def _customer_email(
    *,
    market_code: str,
    ordinal: int,
) -> str:
    return f"customer.{market_code.lower()}.{ordinal:06d}@mail.example"


def _generate_phone(
    *,
    fake: _CustomerFaker,
    rng: random.Random,
    config: CustomerSimulationConfig,
) -> str | None:
    if rng.random() < config.missing_phone_probability:
        return None

    phone: str = (fake.phone_number()).strip()

    if not phone:
        return None

    return phone


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
            0,
            span,
        )
    )


def _group_geography_by_market() -> dict[
    str,
    tuple[CustomerGeography, ...],
]:
    grouped: dict[
        str,
        list[CustomerGeography],
    ] = defaultdict(list)

    for geography in CUSTOMER_GEOGRAPHIES:
        grouped[geography.market_code].append(geography)

    return {market_code: tuple(rows) for market_code, rows in grouped.items()}
