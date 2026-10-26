import random
import string
from datetime import date, timedelta

from mercatura.source.reference.geography import (
    StoreLocation,
    locations_for_market,
)
from mercatura.source.simulation import SimulationContext
from mercatura.source.simulation.market import MarketConfig
from mercatura.source.systems.store.config import (
    DEFAULT_STORE_CONFIG,
    MarketStoreConfig,
)
from mercatura.source.systems.store.model import Store

"""
========================================================================================

STORE GENERATION

========================================================================================
"""


def generate_stores(
    context: SimulationContext,
    *,
    store_config: tuple[MarketStoreConfig, ...] = DEFAULT_STORE_CONFIG,
) -> tuple[Store, ...]:
    stores: list[Store] = []

    for config in store_config:
        stores.extend(
            _generate_market_stores(
                context,
                config,
            )
        )

    return tuple(stores)


def _generate_market_stores(
    context: SimulationContext,
    config: MarketStoreConfig,
) -> list[Store]:
    market: MarketConfig = context.market(market_code=config.market_code)

    rng: random.Random = context.rng(
        namespace="store",
        market_code=config.market_code,
    )

    locations: tuple[StoreLocation, ...] = locations_for_market(market_code=config.market_code)

    if config.store_count > len(locations):
        raise ValueError(
            f"market {config.market_code} requests "
            f"{config.store_count} stores but only "
            f"{len(locations)} locations are configured"
        )

    stores: list[Store] = []

    for index, location in enumerate(
        iterable=locations[: config.store_count],
        start=1,
    ):
        store_code: str = f"{config.market_code}-{index:04d}"

        store_id: str = context.ids.id_for(
            namespace="store",
            key=store_code,
            prefix="sto",
        )

        opening_offset: int = rng.randint(
            a=0,
            b=max(
                0,
                context.config.day_count // 3,
            ),
        )

        opened_at: date = context.config.start_date + timedelta(days=opening_offset)

        store_format: str = rng.choice(seq=config.formats)

        stores.append(
            Store(
                store_id=store_id,
                market_code=config.market_code,
                store_code=store_code,
                store_name=(f"Mercatura {location.city} {store_format.title()}"),
                store_format=store_format,
                city=location.city,
                region=location.region,
                postal_code=_generate_postal_code(
                    rng,
                    location,
                ),
                country_code=market.market_code,
                timezone=location.timezone,
                opened_at=opened_at,
            )
        )

    return stores


def _generate_postal_code(
    rng: random.Random,
    location: StoreLocation,
) -> str:
    market_code: str = location.market_code
    prefix: str = location.postal_prefix

    if market_code == "GB":
        return f"{prefix} {rng.randint(a=0, b=9)}{_letters(rng, count=2)}"

    if market_code in {
        "DE",
        "US",
        "FR",
    }:
        return f"{prefix}{rng.randint(a=0, b=99):02d}"

    if market_code in {
        "CN",
        "RU",
    }:
        return f"{prefix}{rng.randint(a=0, b=999):03d}"

    if market_code == "NO":
        return f"{prefix}{rng.randint(a=0, b=99):02d}"

    if market_code == "JP":
        return f"{prefix}-{rng.randint(a=0, b=9999):04d}"

    if market_code == "KR":
        return f"{prefix}{rng.randint(a=0, b=999):03d}"

    if market_code == "NL":
        return f"{prefix}{rng.randint(a=0, b=9)} {_letters(rng, count=2)}"

    if market_code == "PL":
        return f"{prefix}-{rng.randint(a=0, b=999):03d}"

    raise ValueError(f"unsupported postal-code market: {market_code}")


def _letters(
    rng: random.Random,
    count: int,
) -> str:
    return "".join(rng.choice(seq=string.ascii_uppercase) for _ in range(count))
