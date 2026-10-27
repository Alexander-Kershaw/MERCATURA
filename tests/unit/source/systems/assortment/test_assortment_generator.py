from datetime import date

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.systems.assortment.generator import (
    generate_assortments,
)
from mercatura.source.systems.assortment.model import ProductMarketAssortment
from mercatura.source.systems.assortment.validation import (
    validate_assortments,
)
from mercatura.source.systems.pim.generator import (
    generate_products,
)
from mercatura.source.systems.pim.model import Product


def build_context() -> SimulationContext:
    return SimulationContext.create(
        config=SimulationConfig(
            start_date=date(year=2024, month=1, day=1),
            end_date=date(year=2026, month=12, day=31),
            seed=42,
        )
    )


def test_assortment_generation_is_deterministic() -> None:
    first_context: SimulationContext = build_context()
    second_context: SimulationContext = build_context()

    first_products: tuple[Product, ...] = generate_products(context=first_context)

    second_products: tuple[Product, ...] = generate_products(context=second_context)

    assert generate_assortments(
        context=first_context,
        products=first_products,
    ) == generate_assortments(
        context=second_context,
        products=second_products,
    )


def test_product_market_pairs_are_unique() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)

    assortments: tuple[ProductMarketAssortment, ...] = generate_assortments(
        context,
        products,
    )

    keys: list[tuple[str, str]] = [
        (
            assortment.product_id,
            assortment.market_code,
        )
        for assortment in assortments
    ]

    assert len(keys) == len(set(keys))


def test_all_markets_receive_products() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)

    assortments: tuple[ProductMarketAssortment, ...] = generate_assortments(
        context,
        products,
    )

    markets: set[str] = {assortment.market_code for assortment in assortments}

    assert markets == {market.market_code for market in context.config.markets}


def test_generated_assortments_pass_validation() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)

    assortments: tuple[ProductMarketAssortment, ...] = generate_assortments(
        context,
        products,
    )

    validate_assortments(
        assortments,
        products,
        context,
    )
