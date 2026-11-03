from datetime import date
from decimal import Decimal

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.simulation.demand import (
    DemandProfile,
    generate_demand_profiles,
)
from mercatura.source.simulation.demand_validation import (
    validate_demand_profiles,
)
from mercatura.source.systems.assortment.generator import (
    generate_assortments,
)
from mercatura.source.systems.assortment.model import ProductMarketAssortment
from mercatura.source.systems.pim.generator import (
    generate_products,
)
from mercatura.source.systems.pim.model import Product


def build_dataset() -> tuple[
    SimulationContext,
    tuple[Product, ...],
    tuple[ProductMarketAssortment, ...],
    tuple[DemandProfile, ...],
]:
    context: SimulationContext = SimulationContext.create(
        config=SimulationConfig(
            start_date=date(year=2024, month=1, day=1),
            end_date=date(year=2026, month=12, day=31),
            seed=42,
        )
    )

    products: tuple[Product, ...] = generate_products(context)

    assortments: tuple[ProductMarketAssortment, ...] = generate_assortments(
        context,
        products,
    )

    profiles: tuple[DemandProfile, ...] = generate_demand_profiles(
        context,
        products,
        assortments,
    )

    return (
        context,
        products,
        assortments,
        profiles,
    )


def test_generation_is_deterministic() -> None:
    (
        context,
        products,
        assortments,
        _,
    ) = build_dataset()

    first: tuple[DemandProfile, ...] = generate_demand_profiles(
        context,
        products,
        assortments,
    )

    second: tuple[DemandProfile, ...] = generate_demand_profiles(
        context,
        products,
        assortments,
    )

    assert first == second


def test_every_assortment_has_one_profile() -> None:
    (
        _,
        _,
        assortments,
        profiles,
    ) = build_dataset()

    assert len(profiles) == len(assortments)

    assert len({profile.assortment_id for profile in profiles}) == len(assortments)


def test_daily_demand_is_positive() -> None:
    *_, profiles = build_dataset()

    assert all(profile.average_daily_units > Decimal(value="0") for profile in profiles)


def test_volatility_is_valid() -> None:
    *_, profiles = build_dataset()

    assert all(
        Decimal(value="0") <= profile.volatility <= Decimal(value="1") for profile in profiles
    )


def test_seasonality_is_valid() -> None:
    *_, profiles = build_dataset()

    assert all(
        Decimal(value="0") <= profile.seasonality_strength <= Decimal(value="1")
        for profile in profiles
    )


def test_input_order_does_not_change_profiles() -> None:
    (
        context,
        products,
        assortments,
        _,
    ) = build_dataset()

    first: tuple[DemandProfile, ...] = generate_demand_profiles(
        context,
        products,
        assortments,
    )

    second: tuple[DemandProfile, ...] = generate_demand_profiles(
        context,
        products,
        tuple(reversed(assortments)),
    )

    assert first == second


def test_generated_profiles_pass_validation() -> None:
    (
        _,
        products,
        assortments,
        profiles,
    ) = build_dataset()

    validate_demand_profiles(
        profiles,
        products,
        assortments,
    )
