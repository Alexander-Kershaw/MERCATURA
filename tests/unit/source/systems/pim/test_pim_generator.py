from datetime import date

from mercatura.source.simulation import (
    SimulationConfig,
    SimulationContext,
)
from mercatura.source.systems.pim.generator import (
    generate_products,
)
from mercatura.source.systems.pim.model import Product
from mercatura.source.systems.pim.validation import (
    validate_products,
)


def build_context() -> SimulationContext:
    return SimulationContext.create(
        config=SimulationConfig(
            start_date=date(year=2024, month=1, day=1),
            end_date=date(year=2026, month=12, day=31),
            seed=42,
        )
    )


def test_default_generation_creates_500_products() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)

    assert len(products) == 500


def test_product_generation_is_deterministic() -> None:
    first: tuple[Product, ...] = generate_products(context=build_context())

    second: tuple[Product, ...] = generate_products(context=build_context())

    assert first == second


def test_product_ids_are_unique() -> None:
    products: tuple[Product, ...] = generate_products(context=build_context())

    ids: list[str] = [product.product_id for product in products]

    assert len(ids) == len(set(ids))


def test_skus_are_unique() -> None:
    products: tuple[Product, ...] = generate_products(context=build_context())

    skus: list[str] = [product.sku for product in products]

    assert len(skus) == len(set(skus))


def test_generated_products_pass_validation() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)

    validate_products(
        products,
        context,
    )


def test_catalogue_contains_historical_products() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)

    assert any(product.created_at < context.config.start_date for product in products)


def test_catalogue_contains_new_products() -> None:
    context: SimulationContext = build_context()

    products: tuple[Product, ...] = generate_products(context)

    assert any(
        context.config.start_date <= product.created_at <= context.config.end_date
        for product in products
    )


def test_catalogue_contains_discontinued_products() -> None:
    products: tuple[Product, ...] = generate_products(context=build_context())

    assert any(product.discontinued_at is not None for product in products)
