import random
from datetime import date, timedelta

from faker import Faker

from mercatura.source.reference.geography import (
    StoreLocation,
    locations_for_market,
)
from mercatura.source.simulation import (
    SimulationContext,
)
from mercatura.source.simulation.market import MarketConfig
from mercatura.source.systems.supplier.config import (
    DEFAULT_MARKET_SUPPLIERS,
    DEFAULT_SUPPLIER_CONFIG,
    SUPPLIER_TYPES,
    MarketSupplierConfig,
    SupplierSimulationConfig,
)
from mercatura.source.systems.supplier.faker import (
    build_supplier_faker,
)
from mercatura.source.systems.supplier.model import (
    Supplier,
)


def generate_suppliers(
    context: SimulationContext,
    *,
    market_configs: tuple[MarketSupplierConfig, ...] = DEFAULT_MARKET_SUPPLIERS,
    supplier_config: SupplierSimulationConfig = (DEFAULT_SUPPLIER_CONFIG),
) -> tuple[Supplier, ...]:
    suppliers: list[Supplier] = []

    for market_config in market_configs:
        context.market(market_code=market_config.market_code)

        for supplier_number in range(
            1,
            market_config.supplier_count + 1,
        ):
            suppliers.append(
                _generate_supplier(
                    context=context,
                    market_config=market_config,
                    supplier_number=supplier_number,
                    supplier_config=supplier_config,
                )
            )

    return tuple(suppliers)


def _generate_supplier(
    *,
    context: SimulationContext,
    market_config: MarketSupplierConfig,
    supplier_number: int,
    supplier_config: SupplierSimulationConfig,
) -> Supplier:
    market_code: str = market_config.market_code

    market: MarketConfig = context.market(market_code)

    rng = random.Random(x=context.seed_for(namespace=(f"supplier:{market_code}:{supplier_number}")))

    fake: Faker = build_supplier_faker(
        context,
        market_code=market_code,
        supplier_number=supplier_number,
    )

    supplier_code: str = f"SUP-{market_code}-{supplier_number:04d}"

    supplier_id: str = context.ids.id_for(
        namespace="supplier",
        key=supplier_code,
        prefix="sup",
    )

    locations: tuple[StoreLocation, ...] = locations_for_market(market_code)

    location: StoreLocation = rng.choice(seq=locations)

    legal_name: str = fake.company()

    supplier_type: str = rng.choice(seq=SUPPLIER_TYPES)

    created_at: date = _generate_created_at(
        context=context,
        config=supplier_config,
        rng=rng,
    )

    inactive_at: date | None = _generate_inactive_at(
        context=context,
        created_at=created_at,
        config=supplier_config,
        rng=rng,
    )

    return Supplier(
        supplier_id=supplier_id,
        supplier_code=supplier_code,
        legal_name=legal_name,
        supplier_type=supplier_type,
        country_code=market_code,
        currency=market.currency,
        city=location.city,
        region=location.region,
        created_at=created_at,
        inactive_at=inactive_at,
    )


def _generate_created_at(
    *,
    context: SimulationContext,
    config: SupplierSimulationConfig,
    rng: random.Random,
) -> date:
    if rng.random() < config.onboard_during_simulation_rate:
        return _random_date(
            rng=rng,
            start=context.config.start_date,
            end=context.config.end_date,
        )

    historical_start: date = context.config.start_date - timedelta(days=365 * config.history_years)

    return _random_date(
        rng=rng,
        start=historical_start,
        end=(context.config.start_date - timedelta(days=1)),
    )


def _generate_inactive_at(
    *,
    context: SimulationContext,
    created_at: date,
    config: SupplierSimulationConfig,
    rng: random.Random,
) -> date | None:
    if rng.random() >= config.deactivate_rate:
        return None

    earliest_inactive: date = max(
        created_at + timedelta(days=config.minimum_active_days),
        context.config.start_date,
    )

    if earliest_inactive > context.config.end_date:
        return None

    return _random_date(
        rng=rng,
        start=earliest_inactive,
        end=context.config.end_date,
    )


def _random_date(
    *,
    rng: random.Random,
    start: date,
    end: date,
) -> date:
    if end < start:
        raise ValueError("end must be on or after start")

    day_count: int = (end - start).days

    return start + timedelta(
        days=rng.randint(
            a=0,
            b=day_count,
        )
    )
