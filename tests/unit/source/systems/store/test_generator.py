from collections import Counter
from datetime import date

from mercatura.source.reference.geography import StoreLocation, locations_for_market
from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.systems.store.generator import (
    generate_stores,
)
from mercatura.source.systems.store.model import Store
from mercatura.source.systems.store.validation import (
    validate_stores,
)


def build_context() -> SimulationContext:
    return SimulationContext.create(
        config=SimulationConfig(
            start_date=date(year=2024, month=1, day=1),
            end_date=date(year=2026, month=12, day=31),
            seed=42,
        )
    )


def test_default_store_generation_creates_66_stores() -> None:
    context: SimulationContext = build_context()

    stores: tuple[Store, ...] = generate_stores(context)

    assert len(stores) == 66


def test_store_generation_is_deterministic() -> None:
    first_context: SimulationContext = build_context()
    second_context: SimulationContext = build_context()

    assert generate_stores(context=first_context) == generate_stores(context=second_context)


def test_store_ids_are_unique() -> None:
    context: SimulationContext = build_context()

    stores: tuple[Store, ...] = generate_stores(context)

    ids: list[str] = [store.store_id for store in stores]

    assert len(ids) == len(set(ids))


def test_store_codes_are_unique() -> None:
    context: SimulationContext = build_context()

    stores: tuple[Store, ...] = generate_stores(context)

    codes: list[str] = [store.store_code for store in stores]

    assert len(codes) == len(set(codes))


def test_generated_stores_pass_validation() -> None:
    context: SimulationContext = build_context()

    stores: tuple[Store, ...] = generate_stores(context)

    validate_stores(
        stores,
        context,
    )


def test_store_market_distribution() -> None:
    context: SimulationContext = build_context()

    stores: tuple[Store, ...] = generate_stores(context)

    counts: Counter[str] = Counter(store.market_code for store in stores)

    assert counts == {
        "GB": 12,
        "DE": 7,
        "US": 8,
        "CN": 6,
        "NO": 3,
        "RU": 4,
        "JP": 6,
        "KR": 5,
        "FR": 6,
        "NL": 4,
        "PL": 5,
    }


def test_generated_store_geography_matches_reference() -> None:
    context: SimulationContext = build_context()

    stores: tuple[Store, ...] = generate_stores(context)

    for store in stores:
        locations: tuple[StoreLocation, ...] = locations_for_market(market_code=store.market_code)

        matching: list[StoreLocation] = [
            location for location in locations if location.city == store.city
        ]

        assert len(matching) == 1

        location: StoreLocation = matching[0]

        assert store.region == location.region
        assert store.timezone == location.timezone
