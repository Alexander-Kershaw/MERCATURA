from mercatura.source.simulation import SimulationContext
from mercatura.source.systems.assortment.model import (
    ProductMarketAssortment,
)
from mercatura.source.systems.pim.model import Product


def validate_assortments(
    assortments: tuple[ProductMarketAssortment, ...],
    products: tuple[Product, ...],
    context: SimulationContext,
) -> None:
    _validate_unique_ids(assortments)

    _validate_unique_product_markets(assortments)

    _validate_products_exist(
        assortments,
        products,
    )

    _validate_markets(
        assortments,
        context,
    )

    _validate_lifecycles(
        assortments,
        products,
    )


def _validate_unique_ids(
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    ids: list[str] = [assortment.assortment_id for assortment in assortments]

    if len(ids) != len(set(ids)):
        raise ValueError("duplicate assortment_id detected")


def _validate_unique_product_markets(
    assortments: tuple[ProductMarketAssortment, ...],
) -> None:
    keys: list[tuple[str, str]] = [
        (
            assortment.product_id,
            assortment.market_code,
        )
        for assortment in assortments
    ]

    if len(keys) != len(set(keys)):
        raise ValueError("duplicate product-market assortment detected")


def _validate_products_exist(
    assortments: tuple[ProductMarketAssortment, ...],
    products: tuple[Product, ...],
) -> None:
    product_ids: set[str] = {product.product_id for product in products}

    invalid: set[str] = {
        assortment.product_id
        for assortment in assortments
        if assortment.product_id not in product_ids
    }

    if invalid:
        raise ValueError("assortment references unknown products")


def _validate_markets(
    assortments: tuple[ProductMarketAssortment, ...],
    context: SimulationContext,
) -> None:
    valid_markets: set[str] = {market.market_code for market in context.config.markets}

    invalid: set[str] = {
        assortment.market_code
        for assortment in assortments
        if assortment.market_code not in valid_markets
    }

    if invalid:
        raise ValueError(f"assortment references unknown markets: {sorted(invalid)}")


def _validate_lifecycles(
    assortments: tuple[ProductMarketAssortment, ...],
    products: tuple[Product, ...],
) -> None:
    products_by_id: dict[str, Product] = {product.product_id: product for product in products}

    for assortment in assortments:
        product: Product = products_by_id[assortment.product_id]

        if assortment.ranged_from < product.created_at:
            raise ValueError(f"{assortment.sku} ranged before product creation")

        if assortment.ranged_to is not None and assortment.ranged_to <= assortment.ranged_from:
            raise ValueError(f"{assortment.sku} has invalid assortment lifecycle")

        if (
            product.discontinued_at is not None
            and assortment.ranged_to is not None
            and assortment.ranged_to > product.discontinued_at
        ):
            raise ValueError(f"{assortment.sku} remains ranged after discontinuation")
